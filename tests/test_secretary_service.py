"""Tests for the one-specialist, read-only Secretary conversation boundary."""

import unittest
from io import BytesIO, TextIOWrapper
from types import SimpleNamespace

from jarvis.conversation import ConversationIntent, SecretaryService
from jarvis.chat_cli import _safe_print


def result(**values):
    baseline = {"status": "ok", "reporting_at": None, "headline": "Grounded headline", "alerts": (), "source_references": (), "task_id": "task", "correlation_id": "corr", "terminal_state": "succeeded", "important_items": (), "items": (), "activity": (), "mode": None}
    return SimpleNamespace(**(baseline | values))


class FakeDaily:
    def __init__(self): self.calls = 0
    def get_daily_summary(self): self.calls += 1; return result()
class FakeResearch:
    def __init__(self): self.calls = 0
    def get_summary(self): self.calls += 1; return result(items=("Finding",))
class FakeTrading:
    def __init__(self): self.calls = 0
    def get_context(self): self.calls += 1; return result(mode="paper", activity=("Activity",))


class SecretaryServiceTests(unittest.TestCase):
    def setUp(self):
        self.daily, self.research, self.trading = FakeDaily(), FakeResearch(), FakeTrading()
        self.service = SecretaryService(self.daily, self.research, self.trading)

    def test_routes_one_and_only_one_specialist_and_composes_grounded_text(self):
        response = self.service.respond("Research status")
        self.assertEqual(response.domain, ConversationIntent.RESEARCH)
        self.assertIn("Finding", response.text)
        self.assertEqual((self.daily.calls, self.research.calls, self.trading.calls), (0, 1, 0))

    def test_mutating_and_ambiguous_requests_do_not_call_specialists(self):
        for message in ("Buy this stock", "Research and Trading status"):
            with self.subTest(message=message): self.service.respond(message)
        self.assertEqual((self.daily.calls, self.research.calls, self.trading.calls), (0, 0, 0))

    def test_research_proposal_and_separate_approval_never_call_read_specialists(self):
        proposed = self.service.respond("Start Research on battery recycling")
        self.assertEqual(proposed.domain, ConversationIntent.RESEARCH_MUTATION)
        proposal_id = next(line.split(": ", 1)[1] for line in proposed.text.splitlines() if line.startswith("Proposal ID:"))
        approved = self.service.respond(f"approve {proposal_id}")
        self.assertEqual(approved.terminal_state, "approved_pending_remote_contract")
        self.assertIn("Remote execution is unavailable", approved.text)
        self.assertEqual((self.daily.calls, self.research.calls, self.trading.calls), (0, 0, 0))

    def test_trading_response_preserves_read_only_mode_without_claiming_execution(self):
        response = self.service.respond("Trading status")
        self.assertIn("Mode: paper (read-only context)", response.text)
        self.assertNotIn("executed", response.text.lower())

    def test_windows_legacy_console_output_does_not_raise_for_returned_unicode(self):
        raw = BytesIO()
        stream = TextIOWrapper(raw, encoding="cp932")
        _safe_print("Research status: 🌐", file=stream)
        stream.flush()
        self.assertIn(b"Research status", raw.getvalue())
