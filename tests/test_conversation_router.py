"""Tests for deterministic conversational intent routing."""

import unittest

from jarvis.conversation import ConversationIntent, IntentRouter


class IntentRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = IntentRouter()

    def test_routes_each_supported_read_intent(self) -> None:
        cases = {
            "Show today's daily summary": ConversationIntent.DAILY,
            "What is the Research status?": ConversationIntent.RESEARCH,
            "Trading Lab portfolio status": ConversationIntent.TRADING,
        }
        for message, intent in cases.items():
            with self.subTest(message=message):
                self.assertEqual(self.router.route(message).intent, intent)

    def test_ambiguous_and_unsupported_requests_do_not_select_a_capability(self) -> None:
        self.assertEqual(self.router.route("Research and Trading status").intent, ConversationIntent.CLARIFY)
        self.assertEqual(self.router.route("Tell me a joke").intent, ConversationIntent.UNSUPPORTED)

    def test_mutating_requests_are_blocked_before_any_specialist_selection(self) -> None:
        for message in ("Buy this stock", "Approve this research", "Start a new research job"):
            with self.subTest(message=message):
                self.assertEqual(
                    self.router.route(message).intent, ConversationIntent.READ_ONLY_BOUNDARY
                )

