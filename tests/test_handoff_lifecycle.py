from datetime import UTC, datetime
import unittest

from jarvis.handoff import HandoffEnvelope, StateStore
from jarvis.handoff.lifecycle import CancellationService, RecoveryManager
from jarvis.handoff.loop_prevention import consume_hop, may_invoke_agent
from jarvis.handoff.protocol import ProtocolError
from jarvis.handoff.redaction import redact


class LifecycleTests(unittest.TestCase):
    def store(self):
        store = StateStore(":memory:")
        store.register(message_id="m", correlation_id="c", source_commit_sha="a" * 40, payload_sha256="b" * 64)
        return store
    def test_cancellation_is_idempotent_and_terminal_safe(self):
        store = self.store(); cancelled = CancellationService(store).cancel("m")
        self.assertEqual(cancelled.processing_state, "cancelled")
        self.assertEqual(CancellationService(store).cancel("m"), cancelled)
    def test_recovery_blocks_unfinished_work_deterministically(self):
        recovered = RecoveryManager(self.store()).recover_interrupted()
        self.assertEqual(recovered[0].processing_state, "blocked"); self.assertEqual(recovered[0].error_category, "interrupted")
    def test_hops_responses_and_redaction_are_safe(self):
        message = HandoffEnvelope("m", "c", datetime.now(UTC), "mitir", "jarvis", "status_response", "completed", "r", "L0", False, datetime.now(UTC), 1, {}, (), ())
        self.assertFalse(may_invoke_agent(message)); self.assertEqual(consume_hop(message).max_hops, 0)
        with self.assertRaises(ProtocolError): consume_hop(consume_hop(message))
        self.assertNotIn("abc", redact("Authorization: Bearer abc MITIR_INTEGRATION_TOKEN=xyz"))
