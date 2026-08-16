from datetime import UTC, datetime
import unittest

from jarvis.handoff import HandoffEnvelope, PolicyEngine


def envelope(**changes):
    value = HandoffEnvelope(
        message_id="11111111-1111-4111-8111-111111111111", correlation_id="22222222-2222-4222-8222-222222222222",
        created_at=datetime(2026, 8, 16, tzinfo=UTC), sender="mitir", recipient="jarvis", type="implementation_request",
        status="requested", reply_to=None, execution_level="L2", requires_approval=False,
        expires_at=datetime(2026, 8, 17, tzinfo=UTC), max_hops=3, payload={}, prohibited_actions=(), artifacts=(),
    )
    return value.__class__(**{**value.__dict__, **changes})


class PolicyEngineTests(unittest.TestCase):
    def test_l0_to_l2_without_restrictions_are_accepted(self):
        for level in ("L0", "L1", "L2"):
            self.assertTrue(PolicyEngine().evaluate(envelope(execution_level=level)).allowed)

    def test_approval_kill_switch_and_message_prohibitions_stop_execution(self):
        self.assertEqual(PolicyEngine().evaluate(envelope(requires_approval=True)).status, "approval_required")
        self.assertEqual(PolicyEngine(agent_execution_enabled=False).evaluate(envelope()).status, "blocked")
        self.assertEqual(PolicyEngine().evaluate(envelope(prohibited_actions=("source changes",))).status, "rejected")

    def test_l3_l4_trading_and_live_mutation_are_always_rejected(self):
        for level in ("L3", "L4"):
            self.assertEqual(PolicyEngine().evaluate(envelope(execution_level=level)).status, "rejected")
        for action in ("trading-mutation", "live_mitir_mutation", "RM-T10"):
            self.assertEqual(PolicyEngine().evaluate(envelope(prohibited_actions=(action,))).status, "rejected")

    def test_kill_switch_keeps_l0_inspection_available(self):
        self.assertTrue(PolicyEngine(agent_execution_enabled=False).evaluate(envelope(execution_level="L0")).allowed)
