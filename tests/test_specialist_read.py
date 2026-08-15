"""Tests for shared bounded read-only specialist task execution."""

import unittest

from jarvis.integrations.mitir.daily_summary import DailySummaryError, DailySummaryFailureCategory
from jarvis.integrations.mitir.models import CapabilityList, Health, TaskRecord
from jarvis.integrations.mitir.specialist_read import ReadOnlySpecialistRunner


NOW = "2026-08-15T00:00:00Z"


def record(state: str, correlation_id: str, result=None) -> TaskRecord:
    return TaskRecord.model_validate({"id": "11111111-1111-4111-8111-111111111111", "capability_id": "research.summary", "state": state, "correlation_id": correlation_id, "requester": "jarvis", "result": result, "error": None, "created_at": NOW, "updated_at": NOW, "started_at": None, "completed_at": NOW if state == "succeeded" else None})


class FakeClient:
    def __init__(self, states): self.states, self.request = list(states), None
    def get_health(self): return Health(status="ok", component="secretary", api_version="0.1.0", ready=True)
    def list_capabilities(self): return CapabilityList.model_validate({"api_version": "0.1.0", "capabilities": [{"id": "research.summary", "description": "Research", "version": "1", "available": True, "approval_required": False, "input_schema": "EmptyInput", "output_schema": "Summary"}]})
    def create_task(self, task, *, idempotency_key):
        self.request = task
        return record(self.states.pop(0), task.correlation_id, {"headline": "Research"})
    def get_task(self, task_id): return record(self.states.pop(0), self.request.correlation_id, {"headline": "Research"})


class SpecialistReadTests(unittest.TestCase):
    def test_executes_one_fixed_read_request_with_bounded_polling(self):
        client = FakeClient(["accepted", "succeeded"])
        task, correlation = ReadOnlySpecialistRunner(client, max_attempts=2, poll_interval=0).run("research.summary", {}, requester="jarvis")
        self.assertEqual(client.request.capability_id, "research.summary")
        self.assertEqual(client.request.input, {})
        self.assertEqual(task.state.value, "succeeded")
        self.assertEqual(task.correlation_id, correlation)

    def test_timeout_is_safe_and_bounded(self):
        client = FakeClient(["accepted", "running", "running"])
        with self.assertRaises(DailySummaryError) as caught:
            ReadOnlySpecialistRunner(client, max_attempts=2, poll_interval=0).run("research.summary", {}, requester="jarvis")
        self.assertEqual(caught.exception.category, DailySummaryFailureCategory.TIMEOUT)

