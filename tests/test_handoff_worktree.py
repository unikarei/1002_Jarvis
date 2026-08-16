import subprocess
import unittest
from pathlib import Path

from jarvis.handoff.worktree import WorktreeError, WorktreeManager


class WorktreeManagerTests(unittest.TestCase):
    def test_creates_one_branch_and_worktree_from_pinned_commit(self):
        calls = []
        def runner(args, **_kwargs): calls.append(args); return subprocess.CompletedProcess(args, 0, stdout="")
        result = WorktreeManager("C:/repo", "C:/worktrees", runner=runner).create("11111111-1111-4111-8111-111111111111", "a" * 40)
        self.assertEqual(result.branch_name, "handoff/11111111-1111-4111-8111-111111111111")
        self.assertEqual(calls[0][3:7], ["worktree", "add", "-b", result.branch_name])
        self.assertNotIn("--force", calls[0])

    def test_invalid_or_existing_target_is_not_sent_to_git(self):
        manager = WorktreeManager("C:/repo", "C:/worktrees")
        with self.assertRaises(WorktreeError): manager.create("not-a-uuid", "a" * 40)
        with self.assertRaises(WorktreeError): manager.create("11111111-1111-4111-8111-111111111111", "not-hex")
