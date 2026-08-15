"""Tests for bounded, read-only Trading Context."""

import unittest

from jarvis.integrations.mitir.models import TaskRecord
from jarvis.integrations.mitir.trading_context import DEFAULT_TRADING_LIMIT, TradingContextService

NOW = "2026-08-15T00:00:00Z"


def record(result):
    return TaskRecord.model_validate({"id": "11111111-1111-4111-8111-111111111111", "capability_id": "trading.context", "state": "succeeded", "correlation_id": "corr", "requester": "jarvis", "result": result, "error": None, "created_at": NOW, "updated_at": NOW, "started_at": NOW, "completed_at": NOW})


class FakeRunner:
    def __init__(self): self.calls = []
    def run(self, capability_id, payload, *, requester):
        self.calls.append((capability_id, payload, requester))
        return record({"status": "ok", "mode": "paper", "headline": "Context", "important_items": ["Activity"], "alerts": ["Review"]}), "corr"


class TradingContextTests(unittest.TestCase):
    def test_uses_only_bounded_read_context(self):
        runner = FakeRunner()
        result = TradingContextService(runner).get_context()
        self.assertEqual(runner.calls, [("trading.context", {"limit": DEFAULT_TRADING_LIMIT}, "jarvis")])
        self.assertEqual(result.mode, "paper")
        self.assertEqual(result.activity, ("Activity",))

    def test_rejects_unbounded_limit_locally(self):
        with self.assertRaises(ValueError): TradingContextService(FakeRunner()).get_context(101)
