"""Fake-driven tests for the JARVIS daily-summary application boundary."""

import unittest
from uuid import UUID

from jarvis.integrations.mitir import MiTiRAPIError, MiTiRContractError, MiTiRTransportError
from jarvis.integrations.mitir.daily_summary import (
    DailySummaryError,
    DailySummaryFailureCategory,
    DailySummaryService,
    daily_summary_service_from_environment,
)
from jarvis.integrations.mitir.daily_summary_cli import render_daily_summary
from jarvis.integrations.mitir.models import CapabilityList, Health, TaskError, TaskRecord


TASK_ID = "11111111-1111-4111-8111-111111111111"
NOW = "2026-08-15T00:00:00Z"


def task(state: str, *, correlation_id: str | None = None, result=None) -> TaskRecord:
    return TaskRecord.model_validate({
        "id": TASK_ID, "capability_id": "daily.summary", "state": state,
        "correlation_id": correlation_id, "requester": "jarvis", "result": result,
        "error": None, "created_at": NOW, "updated_at": NOW,
        "started_at": NOW if state != "accepted" else None,
        "completed_at": NOW if state in {"succeeded", "failed", "cancelled"} else None,
    })


class FakeClient:
    def __init__(self, *, health_ready=True, available=True, states=None, result=None, error=None) -> None:
        self.health_ready, self.available = health_ready, available
        self.states = list(states or ["succeeded"])
        self.result, self.error = result if result is not None else {}, error
        self.correlation_id = None
        self.requests = []

    def get_health(self):
        if self.error:
            raise self.error
        return Health(status="ok", component="secretary", api_version="0.1.0", ready=self.health_ready)

    def list_capabilities(self):
        return CapabilityList.model_validate({"api_version": "0.1.0", "capabilities": [{
            "id": "daily.summary", "description": "Daily", "version": "1", "available": self.available,
            "approval_required": False, "input_schema": "EmptyInput", "output_schema": "Summary",
        }]})

    def create_task(self, request, *, idempotency_key):
        self.requests.append((request, idempotency_key))
        self.correlation_id = request.correlation_id
        return task(self.states.pop(0), correlation_id=self.correlation_id, result=self.result)

    def get_task(self, task_id):
        self.assert_task_id(task_id)
        return task(self.states.pop(0), correlation_id=self.correlation_id, result=self.result)

    @staticmethod
    def assert_task_id(task_id):
        assert UUID(task_id) == UUID(TASK_ID)


class DailySummaryServiceTests(unittest.TestCase):
    def service(self, client, *, attempts=2):
        return DailySummaryService(client, max_attempts=attempts, poll_interval=0)

    def test_maps_available_summary_and_hides_task_mechanics(self):
        client = FakeClient(states=["accepted", "succeeded"], result={
            "status": "ok", "reporting_at": NOW, "headline": "Focus on the launch.",
            "important_items": [{"title": "Ship"}], "alerts": ["Review risk"],
            "source_artifacts": ["daily.md"],
        })
        result = self.service(client).get_daily_summary()
        self.assertEqual(result.headline, "Focus on the launch.")
        self.assertEqual(result.important_items, ({"title": "Ship"},))
        self.assertEqual(result.alerts, ("Review risk",))
        self.assertEqual(result.source_references, ("daily.md",))
        self.assertEqual(client.requests[0][0].capability_id, "daily.summary")
        self.assertEqual(client.requests[0][0].input, {})
        self.assertTrue(result.correlation_id.startswith("jarvis-daily-summary-"))

    def test_missing_optional_result_fields_are_not_fabricated(self):
        result = self.service(FakeClient()).get_daily_summary()
        self.assertIsNone(result.reporting_at)
        self.assertIsNone(result.headline)
        self.assertEqual(result.important_items, ())
        self.assertEqual(result.alerts, ())
        self.assertEqual(result.source_references, ())

    def test_not_ready_and_capability_unavailable_are_stable_categories(self):
        for client, category in (
            (FakeClient(health_ready=False), DailySummaryFailureCategory.NOT_READY),
            (FakeClient(available=False), DailySummaryFailureCategory.CAPABILITY_UNAVAILABLE),
        ):
            with self.subTest(category=category), self.assertRaises(DailySummaryError) as caught:
                self.service(client).get_daily_summary()
            self.assertEqual(caught.exception.category, category)

    def test_missing_or_invalid_runtime_configuration_is_safe(self):
        for environment in ({}, {"MITIR_BASE_URL": "not-a-url", "MITIR_INTEGRATION_TOKEN": "secret"}):
            with self.subTest(environment=environment), self.assertRaises(DailySummaryError) as caught:
                daily_summary_service_from_environment(environment)
            self.assertEqual(caught.exception.category, DailySummaryFailureCategory.CONFIGURATION)
            self.assertNotIn("secret", str(caught.exception))

    def test_transport_unauthorized_contract_timeout_and_failed_task_are_mapped(self):
        unauthorized = MiTiRAPIError(401, TaskError(code="unauthorized", message="hidden", retryable=False))
        cases = (
            (FakeClient(error=MiTiRTransportError("network")), 2, DailySummaryFailureCategory.UNREACHABLE),
            (FakeClient(error=MiTiRContractError("bad")), 2, DailySummaryFailureCategory.CONTRACT),
            (FakeClient(error=unauthorized), 2, DailySummaryFailureCategory.UNAUTHORIZED),
            (FakeClient(states=["accepted", "running", "running"]), 2, DailySummaryFailureCategory.TIMEOUT),
            (FakeClient(states=["failed"]), 2, DailySummaryFailureCategory.TASK_FAILED),
        )
        for client, attempts, category in cases:
            with self.subTest(category=category), self.assertRaises(DailySummaryError) as caught:
                self.service(client, attempts=attempts).get_daily_summary()
            self.assertEqual(caught.exception.category, category)
            self.assertNotIn("Bearer", str(caught.exception))
            self.assertNotIn("hidden", str(caught.exception))

    def test_malformed_summary_is_a_contract_error(self):
        with self.assertRaises(DailySummaryError) as caught:
            self.service(FakeClient(result={"headline": ["not text"]})).get_daily_summary()
        self.assertEqual(caught.exception.category, DailySummaryFailureCategory.CONTRACT)

    def test_presentation_is_readable_and_not_raw_task_json(self):
        result = self.service(FakeClient(result={
            "reporting_at": NOW, "headline": "Focus on the launch.",
            "important_items": [{"title": "Ship the review", "internal": "ignored"}],
            "alerts": ["Review risk"], "source_artifacts": ["daily.md"],
        })).get_daily_summary()
        rendered = render_daily_summary(result)
        self.assertIn("Daily Intelligence", rendered)
        self.assertIn("Ship the review", rendered)
        self.assertIn("Review risk", rendered)
        self.assertNotIn('"task_id"', rendered)
        self.assertNotIn(result.task_id, rendered)
