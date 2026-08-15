"""Tests for the opt-in MiTiR verification workflow."""

import unittest
from uuid import UUID

from jarvis.integrations.mitir import MiTiRAPIError, TaskRequest
from jarvis.integrations.mitir.models import (
    CapabilityList,
    Health,
    TaskError,
    TaskRecord,
)
from jarvis.integrations.mitir.verify import run_verification


TASK_ID = "11111111-1111-4111-8111-111111111111"
NOW = "2026-08-14T00:00:00Z"


def record(*, result=None) -> TaskRecord:
    return TaskRecord.model_validate({
        "id": TASK_ID, "capability_id": "daily.summary", "state": "succeeded",
        "correlation_id": None, "requester": "jarvis", "result": result, "error": None,
        "created_at": NOW, "updated_at": NOW, "started_at": NOW, "completed_at": NOW,
    })


class FakeVerificationClient:
    def __init__(self) -> None:
        self.task = record(result={"summary": "safe"})
        self.created: list[TaskRequest] = []

    def get_health(self) -> Health:
        return Health(status="ok", component="secretary", api_version="0.1.0", ready=True)

    def list_capabilities(self) -> CapabilityList:
        return CapabilityList.model_validate({"api_version": "0.1.0", "capabilities": [
            {"id": name, "description": name, "version": "1", "available": True,
             "approval_required": False, "input_schema": "{}", "output_schema": "{}"}
            for name in ("daily.summary", "research.summary", "trading.context")
        ]})

    def create_task(self, task: TaskRequest, *, idempotency_key: str) -> TaskRecord:
        self.created.append(task)
        if len(self.created) == 3:
            raise MiTiRAPIError(409, TaskError(
                code="idempotency_conflict", message="changed", retryable=False,
            ))
        return self.task.model_copy(update={"correlation_id": task.correlation_id})

    def get_task(self, task_id: str) -> TaskRecord:
        assert task_id == TASK_ID
        return self.task

    def cancel_task(self, task_id: str) -> TaskRecord:
        assert UUID(task_id) == UUID(TASK_ID)
        return self.task


class VerificationTests(unittest.TestCase):
    def test_workflow_uses_empty_inputs_and_a_rejected_research_conflict_probe(self) -> None:
        client = FakeVerificationClient()
        evidence = run_verification(client, destination="http://mitir.tailnet:8080", poll_interval=0)
        self.assertEqual([request.input for request in client.created], [{}, {}, {}])
        self.assertEqual(
            [request.capability_id for request in client.created],
            ["daily.summary", "daily.summary", "research.summary"],
        )
        self.assertEqual([request.requester for request in client.created], ["jarvis"] * 3)
        self.assertEqual(evidence.final_state, "succeeded")
        self.assertTrue(evidence.exact_replay_same_task_id)
        self.assertEqual(evidence.changed_replay_status, 409)
        self.assertFalse(evidence.changed_replay_retryable)
        self.assertTrue(evidence.terminal_cancel_retained_result)
        self.assertNotIn("token", str(evidence).lower())
