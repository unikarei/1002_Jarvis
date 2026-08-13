"""Consumer contract tests for MiTiR Integration API v0.1.0."""

import json
import unittest
from collections import deque
from pathlib import Path
from typing import Mapping
from uuid import UUID

import yaml

from jarvis.integrations.mitir import MiTiRAPIError, MiTiRClient, TaskRequest, TaskState
from jarvis.integrations.mitir.client import HTTPResponse


TASK_ID = "11111111-1111-4111-8111-111111111111"
NOW = "2026-08-14T00:00:00Z"


class FakeTransport:
    def __init__(self, *responses: tuple[int, dict]) -> None:
        self.responses = deque(responses)
        self.requests: list[dict] = []

    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HTTPResponse:
        self.requests.append(
            {"method": method, "url": url, "headers": dict(headers), "body": body, "timeout": timeout}
        )
        status, payload = self.responses.popleft()
        return HTTPResponse(status, json.dumps(payload).encode())


def task_record(state: str = "accepted") -> dict:
    return {
        "id": TASK_ID,
        "capability_id": "daily.summary",
        "state": state,
        "correlation_id": "corr-1",
        "requester": "jarvis",
        "result": None,
        "error": None,
        "created_at": NOW,
        "updated_at": NOW,
        "started_at": None,
        "completed_at": None,
    }


class MiTiRClientContractTests(unittest.TestCase):
    def client(self, transport: FakeTransport) -> MiTiRClient:
        return MiTiRClient(
            "http://mitir.tailnet:8000", "secret", transport=transport, retry_backoff=0
        )

    def test_health_is_public_and_validated(self) -> None:
        transport = FakeTransport((200, {"status": "ok", "component": "secretary", "api_version": "0.1.0", "ready": True}))
        health = self.client(transport).get_health()
        self.assertTrue(health.ready)
        self.assertNotIn("Authorization", transport.requests[0]["headers"])

    def test_capabilities_use_bearer_auth(self) -> None:
        payload = {
            "api_version": "0.1.0",
            "capabilities": [{
                "id": "daily.summary", "description": "Daily summary", "version": "1",
                "available": True, "approval_required": False,
                "input_schema": "EmptyInput", "output_schema": "Summary",
            }],
        }
        transport = FakeTransport((200, payload))
        capabilities = self.client(transport).list_capabilities()
        self.assertEqual(capabilities.capabilities[0].id, "daily.summary")
        self.assertEqual(transport.requests[0]["headers"]["Authorization"], "Bearer secret")

    def test_create_task_sends_exact_idempotency_key_and_accepts_202(self) -> None:
        transport = FakeTransport((202, task_record()))
        task = self.client(transport).create_task(
            TaskRequest(capability_id="daily.summary", input={}, correlation_id="corr-1", requester="jarvis"),
            idempotency_key="stable-key",
        )
        sent = transport.requests[0]
        self.assertEqual(task.state, TaskState.ACCEPTED)
        self.assertEqual(sent["headers"]["Idempotency-Key"], "stable-key")
        self.assertEqual(json.loads(sent["body"])["capability_id"], "daily.summary")

    def test_exact_idempotent_retry_accepts_200(self) -> None:
        transport = FakeTransport((200, task_record()))
        task = self.client(transport).create_task(
            TaskRequest(capability_id="daily.summary", input={}), idempotency_key="stable-key"
        )
        self.assertEqual(task.id, UUID(TASK_ID))

    def test_idempotency_conflict_maps_error_envelope(self) -> None:
        transport = FakeTransport((409, {"error": {"code": "idempotency_conflict", "message": "payload changed", "retryable": False, "task_id": TASK_ID, "correlation_id": "corr-1"}}))
        with self.assertRaises(MiTiRAPIError) as caught:
            self.client(transport).create_task(
                TaskRequest(capability_id="daily.summary", input={}), idempotency_key="stable-key"
            )
        self.assertEqual(caught.exception.status_code, 409)
        self.assertFalse(caught.exception.error.retryable)

    def test_get_and_cancel_use_uuid_paths(self) -> None:
        transport = FakeTransport((200, task_record("running")), (200, task_record("cancel_requested")))
        client = self.client(transport)
        self.assertEqual(client.get_task(TASK_ID).state, TaskState.RUNNING)
        self.assertEqual(client.cancel_task(TASK_ID).state, TaskState.CANCEL_REQUESTED)
        self.assertTrue(transport.requests[0]["url"].endswith(f"/tasks/{TASK_ID}"))
        self.assertTrue(transport.requests[1]["url"].endswith(f"/tasks/{TASK_ID}/cancel"))

    def test_openapi_snapshot_has_required_operations_and_contract_version(self) -> None:
        contract = yaml.safe_load(
            (Path(__file__).parents[2] / "docs" / "api" / "jarvis-mitir-openapi.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["info"]["version"], "0.1.0")
        self.assertEqual(
            set(contract["paths"]),
            {"/health", "/capabilities", "/tasks", "/tasks/{id}", "/tasks/{id}/cancel"},
        )
        create = contract["paths"]["/tasks"]["post"]
        self.assertIn("Idempotency-Key", {item["name"] for item in create["parameters"]})
        self.assertEqual(set(create["responses"]), {"200", "202", "400", "401", "409"})


if __name__ == "__main__":
    unittest.main()
