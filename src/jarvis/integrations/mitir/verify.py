"""Opt-in, non-destructive verification of the MiTiR v0.1.0 integration API."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from .client import MiTiRClient
from .errors import MiTiRAPIError
from .models import TaskRecord, TaskRequest, TaskState


TERMINAL_STATES = {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}
REQUIRED_CAPABILITIES = {"daily.summary", "research.summary", "trading.context"}


class VerificationClient(Protocol):
    def get_health(self): ...
    def list_capabilities(self): ...
    def create_task(self, task: TaskRequest, *, idempotency_key: str) -> TaskRecord: ...
    def get_task(self, task_id: str) -> TaskRecord: ...
    def cancel_task(self, task_id: str) -> TaskRecord: ...


@dataclass(frozen=True)
class VerificationEvidence:
    tested_at: str
    destination: str
    api_version: str
    health_ready: bool
    capabilities: list[str]
    task_id: str
    correlation_id: str
    final_state: str
    exact_replay_same_task_id: bool
    changed_replay_status: int
    changed_replay_code: str
    changed_replay_retryable: bool
    terminal_cancel_state: str
    terminal_cancel_retained_result: bool


def run_verification(
    client: VerificationClient,
    *,
    destination: str,
    max_attempts: int = 12,
    poll_interval: float = 2.0,
    sleep=time.sleep,
) -> VerificationEvidence:
    """Run the approved daily.summary workflow and a rejected non-destructive conflict probe."""
    if max_attempts < 1 or poll_interval < 0:
        raise ValueError("max_attempts must be at least 1 and poll_interval non-negative")

    health = client.get_health()
    if not health.ready or health.api_version != "0.1.0":
        raise RuntimeError("MiTiR health is not ready for API v0.1.0")

    capabilities = client.list_capabilities()
    capability_ids = {capability.id for capability in capabilities.capabilities}
    missing = REQUIRED_CAPABILITIES - capability_ids
    if capabilities.api_version != "0.1.0" or missing:
        raise RuntimeError("MiTiR capabilities do not match API v0.1.0")

    correlation_id = f"jarvis-phase1-{uuid4()}"
    idempotency_key = f"jarvis-phase1-{uuid4()}"
    request = TaskRequest(
        capability_id="daily.summary", input={}, correlation_id=correlation_id, requester="jarvis"
    )
    task = client.create_task(request, idempotency_key=idempotency_key)

    for _ in range(max_attempts):
        if task.state in TERMINAL_STATES:
            break
        sleep(poll_interval)
        task = client.get_task(str(task.id))
    else:
        raise TimeoutError(f"MiTiR task did not reach a terminal state: {task.id}")

    if task.state is not TaskState.SUCCEEDED:
        raise RuntimeError(f"MiTiR task did not succeed: {task.state}")
    if task.correlation_id != correlation_id:
        raise RuntimeError("MiTiR task did not preserve the correlation ID")

    replay = client.create_task(request, idempotency_key=idempotency_key)
    if replay.id != task.id:
        raise RuntimeError("exact idempotent replay returned a different task ID")

    try:
        client.create_task(
            TaskRequest(
                capability_id="research.summary", input={}, correlation_id=correlation_id,
                requester="jarvis",
            ),
            idempotency_key=idempotency_key,
        )
    except MiTiRAPIError as exc:
        if exc.status_code != 409 or exc.error.code != "idempotency_conflict" or exc.error.retryable:
            raise RuntimeError("changed idempotent replay did not return non-retryable conflict") from exc
        conflict_status, conflict_code, conflict_retryable = (
            exc.status_code, exc.error.code, exc.error.retryable,
        )
    else:
        raise RuntimeError("changed idempotent replay did not return HTTP 409")

    cancelled = client.cancel_task(str(task.id))
    if cancelled.state is not TaskState.SUCCEEDED or cancelled.result != task.result:
        raise RuntimeError("terminal cancellation did not retain successful task and result")

    return VerificationEvidence(
        tested_at=datetime.now(UTC).isoformat(), destination=destination,
        api_version=health.api_version, health_ready=health.ready,
        capabilities=sorted(capability_ids), task_id=str(task.id), correlation_id=correlation_id,
        final_state=task.state.value, exact_replay_same_task_id=True,
        changed_replay_status=conflict_status, changed_replay_code=conflict_code,
        changed_replay_retryable=conflict_retryable, terminal_cancel_state=cancelled.state.value,
        terminal_cancel_retained_result=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-attempts", type=int, default=12)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    args = parser.parse_args()
    base_url = os.environ.get("MITIR_BASE_URL")
    token = os.environ.get("MITIR_INTEGRATION_TOKEN")
    if not base_url or not token:
        parser.error("MITIR_BASE_URL and MITIR_INTEGRATION_TOKEN must be set; live verification was not run")
    evidence = run_verification(
        MiTiRClient(base_url, token), destination=base_url,
        max_attempts=args.max_attempts, poll_interval=args.poll_interval,
    )
    print(json.dumps(asdict(evidence), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
