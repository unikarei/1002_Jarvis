"""Bounded agent-executor interface and non-interactive Codex adapter."""
from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Protocol


@dataclass(frozen=True)
class AgentResult:
    succeeded: bool
    summary: str
    timed_out: bool = False


class AgentExecutor(Protocol):
    def execute(self, prompt: str, *, cwd: str, timeout_seconds: int) -> AgentResult: ...


class MockAgentExecutor:
    def __init__(self, result: AgentResult = AgentResult(True, "mock agent completed")) -> None:
        self.result, self.prompts = result, []
    def execute(self, prompt: str, *, cwd: str, timeout_seconds: int) -> AgentResult:
        self.prompts.append((prompt, cwd, timeout_seconds)); return self.result


class CodexAgentExecutor:
    """Adapter only; the runner invokes it after policy approval, never at import time."""
    def __init__(self, *, runner=subprocess.run, command: tuple[str, ...] = ("codex", "exec", "--json")) -> None:
        self._runner, self._command = runner, command
    def execute(self, prompt: str, *, cwd: str, timeout_seconds: int) -> AgentResult:
        try:
            result = self._runner([*self._command, prompt], cwd=cwd, capture_output=True, text=True, check=False, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            return AgentResult(False, "Agent execution timed out.", timed_out=True)
        if result.returncode != 0: return AgentResult(False, "Non-interactive agent execution failed.")
        return AgentResult(True, result.stdout.strip() or "Agent completed without structured output.")
