import unittest

from jarvis.handoff import StateConflictError, StateStore


class StateStoreTests(unittest.TestCase):
    def test_register_replay_conflict_and_record_update(self):
        store = StateStore(":memory:")
        first, replay = store.register(message_id="m-1", correlation_id="c-1", source_commit_sha="a" * 40, payload_sha256="b" * 64)
        self.assertFalse(replay)
        self.assertEqual(first.processing_state, "accepted")
        same, replay = store.register(message_id="m-1", correlation_id="c-1", source_commit_sha="a" * 40, payload_sha256="b" * 64)
        self.assertTrue(replay)
        self.assertEqual(same.message_id, first.message_id)
        with self.assertRaises(StateConflictError):
            store.register(message_id="m-1", correlation_id="c-1", source_commit_sha="a" * 40, payload_sha256="c" * 64)
        updated = store.update("m-1", processing_state="completed", attempt_count=1, worktree_path="C:/worktrees/m-1", branch_name="handoff/m-1", test_result_summary="passed", finished=True)
        self.assertEqual(updated.processing_state, "completed")
        self.assertEqual(updated.attempt_count, 1)
        self.assertIsNotNone(updated.finished_at)

    def test_unknown_update_does_not_create_state(self):
        store = StateStore(":memory:")
        with self.assertRaises(KeyError):
            store.update("absent", processing_state="failed")
