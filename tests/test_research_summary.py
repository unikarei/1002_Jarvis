"""Tests for the read-only JARVIS Research Summary use case."""

import unittest

from jarvis.integrations.mitir.daily_summary import DailySummaryError, DailySummaryFailureCategory
from jarvis.integrations.mitir.models import TaskRecord
from jarvis.integrations.mitir.research_summary import ResearchSummaryService, research_summary_service_from_environment


NOW = "2026-08-15T00:00:00Z"
TASK_ID = "11111111-1111-4111-8111-111111111111"


def record(result) -> TaskRecord:
    return TaskRecord.model_validate({
        "id": TASK_ID, "capability_id": "research.summary", "state": "succeeded", "correlation_id": "corr",
        "requester": "jarvis", "result": result, "error": None, "created_at": NOW, "updated_at": NOW,
        "started_at": NOW, "completed_at": NOW,
    })


class FakeRunner:
    def __init__(self, task):
        self.task, self.calls = task, []

    def run(self, capability_id, payload, *, requester):
        self.calls.append((capability_id, payload, requester))
        return self.task, "corr"


class ResearchSummaryTests(unittest.TestCase):
    def test_uses_only_read_research_summary_and_maps_present_fields(self):
        runner = FakeRunner(record({
            "status": "ok", "reporting_at": NOW, "headline": "Research ready",
            "important_items": ["Finding"], "alerts": ["Review"], "source_artifacts": ["note.md"],
        }))
        result = ResearchSummaryService(runner).get_summary()
        self.assertEqual(runner.calls, [("research.summary", {}, "jarvis")])
        self.assertEqual(result.headline, "Research ready")
        self.assertEqual(result.items, ("Finding",))
        self.assertEqual(result.source_references, ("note.md",))

    def test_missing_optional_fields_are_not_fabricated(self):
        result = ResearchSummaryService(FakeRunner(record({}))).get_summary()
        self.assertIsNone(result.headline)
        self.assertEqual(result.items, ())
        self.assertEqual(result.alerts, ())

    def test_invalid_result_is_a_safe_contract_error(self):
        with self.assertRaises(DailySummaryError) as caught:
            ResearchSummaryService(FakeRunner(record({"alerts": "not-a-list"}))).get_summary()
        self.assertEqual(caught.exception.category, DailySummaryFailureCategory.CONTRACT)

    def test_missing_runtime_configuration_is_safe(self):
        with self.assertRaises(DailySummaryError) as caught:
            research_summary_service_from_environment({})
        self.assertEqual(caught.exception.category, DailySummaryFailureCategory.CONFIGURATION)
