import subprocess
import unittest

from jarvis.handoff import GitTransport, GitTransportError


class FakeGit:
    def __init__(self, outputs, failure_at=None):
        self.outputs, self.failure_at, self.calls = outputs, failure_at, []

    def __call__(self, args, **_kwargs):
        self.calls.append(args)
        index = len(self.calls) - 1
        return subprocess.CompletedProcess(args, 1 if index == self.failure_at else 0, stdout="" if index == self.failure_at else self.outputs[index], stderr="secret-free test error")


class GitTransportTests(unittest.TestCase):
    sha = "a" * 40

    def test_fetches_origin_main_and_reads_a_pinned_document(self):
        fake = FakeGit(["", self.sha + "\n", "# From MiTiR\n"])
        document = GitTransport("C:/monitoring-clone", runner=fake).fetch_document_if_changed(previous_source_commit_sha=None, document_path="docs/from-MiTiR.md")
        self.assertEqual(document.source_commit_sha, self.sha)
        self.assertEqual(document.content, "# From MiTiR\n")
        commands = [call[3] for call in fake.calls]
        self.assertEqual(commands, ["fetch", "rev-parse", "show"])
        self.assertNotIn("pull", commands)
        self.assertNotIn("push", commands)

    def test_unchanged_sha_skips_document_read(self):
        fake = FakeGit(["", self.sha + "\n"])
        result = GitTransport("C:/monitoring-clone", runner=fake).fetch_document_if_changed(previous_source_commit_sha=self.sha, document_path="docs/from-MiTiR.md")
        self.assertIsNone(result)
        self.assertEqual(len(fake.calls), 2)

    def test_invalid_path_and_git_failure_are_safe(self):
        transport = GitTransport("C:/monitoring-clone", runner=FakeGit([]))
        with self.assertRaises(ValueError): transport.read_file_at(self.sha, "../outside.md")
        with self.assertRaises(GitTransportError):
            GitTransport("C:/monitoring-clone", runner=FakeGit([""], failure_at=0)).fetch_origin_main()
