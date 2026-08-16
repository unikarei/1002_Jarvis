"""Isolated task worktree management; no force or cleanup operations."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable
from uuid import UUID


class WorktreeError(RuntimeError):
    pass


@dataclass(frozen=True)
class TaskWorktree:
    message_id: str
    branch_name: str
    path: Path


class WorktreeManager:
    def __init__(self, repository: Path | str, worktree_root: Path | str, *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self._repository, self._root, self._runner = Path(repository), Path(worktree_root), runner

    def create(self, message_id: str, source_commit_sha: str) -> TaskWorktree:
        try: UUID(message_id)
        except ValueError as exc: raise WorktreeError("Message ID must be a UUID.") from exc
        if not source_commit_sha or any(char not in "0123456789abcdefABCDEF" for char in source_commit_sha):
            raise WorktreeError("Source commit SHA is invalid.")
        branch, path = f"handoff/{message_id}", self._root / message_id
        if path.exists(): raise WorktreeError("Task worktree path already exists.")
        result = self._runner(["git", "-C", str(self._repository), "worktree", "add", "-b", branch, str(path), source_commit_sha], capture_output=True, text=True, check=False)
        if result.returncode != 0: raise WorktreeError("Unable to create isolated task worktree.")
        return TaskWorktree(message_id, branch, path)
