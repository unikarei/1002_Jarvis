import subprocess
import unittest

from jarvis.handoff.executor import AgentResult, CodexAgentExecutor, MockAgentExecutor


class ExecutorTests(unittest.TestCase):
    def test_mock_executor_captures_bounded_invocation(self):
        executor = MockAgentExecutor(AgentResult(True, "done"))
        self.assertTrue(executor.execute("prompt", cwd="C:/task", timeout_seconds=30).succeeded)
        self.assertEqual(executor.prompts, [("prompt", "C:/task", 30)])

    def test_codex_adapter_is_noninteractive_and_handles_timeout(self):
        calls = []
        def runner(args, **kwargs): calls.append((args, kwargs)); return subprocess.CompletedProcess(args, 0, stdout='{"summary":"ok"}')
        result = CodexAgentExecutor(runner=runner).execute("prompt", cwd="C:/task", timeout_seconds=30)
        self.assertTrue(result.succeeded); self.assertEqual(calls[0][0][:3], ["codex", "exec", "--json"])
        def timeout(*_args, **_kwargs): raise subprocess.TimeoutExpired("codex", 30)
        self.assertTrue(CodexAgentExecutor(runner=timeout).execute("prompt", cwd="C:/task", timeout_seconds=30).timed_out)
