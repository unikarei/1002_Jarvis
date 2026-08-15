"""Shared bounded runner for Phase 3 read-only MiTiR specialist capabilities."""

from __future__ import annotations

import time
from typing import Any, Protocol
from uuid import uuid4

from .daily_summary import DailySummaryError, DailySummaryFailureCategory
from .errors import MiTiRAPIError, MiTiRContractError, MiTiRTransportError
from .models import TaskRecord, TaskRequest, TaskState


class SpecialistClient(Protocol):
    def get_health(self): ...
    def list_capabilities(self): ...
    def create_task(self, task: TaskRequest, *, idempotency_key: str) -> TaskRecord: ...
    def get_task(self, task_id: str) -> TaskRecord: ...


class ReadOnlySpecialistRunner:
    """Executes one fixed read capability through the existing typed client."""

    def __init__(self, client: SpecialistClient, *, max_attempts: int = 12, poll_interval: float = 2.0, sleep=time.sleep) -> None:
        if max_attempts < 1 or poll_interval < 0:
            raise ValueError("max_attempts must be at least 1 and poll_interval non-negative")
        self._client, self._max_attempts, self._poll_interval, self._sleep = client, max_attempts, poll_interval, sleep

    def run(self, capability_id: str, payload: dict[str, Any], *, requester: str) -> tuple[TaskRecord, str]:
        correlation_id = f"jarvis-{capability_id.replace('.', '-')}-{uuid4()}"
        try:
            health = self._client.get_health()
            if not health.ready:
                raise DailySummaryError(DailySummaryFailureCategory.NOT_READY, "MiTiR is not ready")
            capabilities = self._client.list_capabilities()
            if not any(item.id == capability_id and item.available for item in capabilities.capabilities):
                raise DailySummaryError(DailySummaryFailureCategory.CAPABILITY_UNAVAILABLE, "Requested MiTiR capability is unavailable")
            task = self._client.create_task(
                TaskRequest(capability_id=capability_id, input=payload, correlation_id=correlation_id, requester=requester),
                idempotency_key=f"{correlation_id}-request",
            )
        except DailySummaryError:
            raise
        except MiTiRAPIError as exc:
            raise _map_api_error(exc, correlation_id) from exc
        except MiTiRContractError as exc:
            raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR returned an invalid response") from exc
        except MiTiRTransportError as exc:
            raise DailySummaryError(DailySummaryFailureCategory.UNREACHABLE, "MiTiR is unreachable") from exc

        for _ in range(self._max_attempts):
            if task.state in {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}:
                break
            self._sleep(self._poll_interval)
            try:
                task = self._client.get_task(str(task.id))
            except MiTiRAPIError as exc:
                raise _map_api_error(exc, correlation_id) from exc
            except MiTiRContractError as exc:
                raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR returned an invalid response") from exc
            except MiTiRTransportError as exc:
                raise DailySummaryError(DailySummaryFailureCategory.UNREACHABLE, "MiTiR is unreachable") from exc
        else:
            raise DailySummaryError(DailySummaryFailureCategory.TIMEOUT, "MiTiR specialist read timed out", task_id=str(task.id), correlation_id=correlation_id)
        if task.state is not TaskState.SUCCEEDED:
            raise DailySummaryError(DailySummaryFailureCategory.TASK_FAILED, "MiTiR specialist read did not succeed", task_id=str(task.id), correlation_id=correlation_id)
        if task.correlation_id != correlation_id or task.result is None:
            raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR specialist response was incomplete", task_id=str(task.id), correlation_id=correlation_id)
        return task, correlation_id


def _map_api_error(exc: MiTiRAPIError, correlation_id: str) -> DailySummaryError:
    category = DailySummaryFailureCategory.UNAUTHORIZED if exc.status_code == 401 else DailySummaryFailureCategory.CONTRACT
    message = "MiTiR authorization failed" if category is DailySummaryFailureCategory.UNAUTHORIZED else "MiTiR rejected the request"
    return DailySummaryError(category, message, task_id=exc.error.task_id, correlation_id=exc.error.correlation_id or correlation_id)
