"""Read-only Git transport for a dedicated monitoring clone."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
import subprocess
from typing import Callable


class GitTransportError(RuntimeError):
    """Safe transport failure without command output or credential disclosure."""


@dataclass(frozen=True)
class RemoteDocument:
    source_commit_sha: str
    content: str


class GitTransport:
    """Fetch `origin/main` in a monitoring clone; never pull, push, or alter worktrees."""

    def __init__(self, monitoring_clone: str, *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self._clone = monitoring_clone
        self._runner = runner

    def fetch_origin_main(self) -> str:
        self._run("fetch", "--prune", "origin", "main")
        sha = self._run("rev-parse", "refs/remotes/origin/main").strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", sha):
            raise GitTransportError("Remote main SHA is invalid.")
        return sha.lower()

    def fetch_document_if_changed(self, *, previous_source_commit_sha: str | None, document_path: str) -> RemoteDocument | None:
        sha = self.fetch_origin_main()
        if sha == previous_source_commit_sha:
            return None
        return RemoteDocument(sha, self.read_file_at(sha, document_path))

    def read_file_at(self, commit_sha: str, document_path: str) -> str:
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", commit_sha):
            raise ValueError("Commit SHA must be hexadecimal.")
        path = PurePosixPath(document_path.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
            raise ValueError("Document path must be a repository-relative path.")
        return self._run("show", f"{commit_sha}:{path.as_posix()}")

    def _run(self, *args: str) -> str:
        result = self._runner(["git", "-C", self._clone, *args], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise GitTransportError("Git command failed.")
        return result.stdout
