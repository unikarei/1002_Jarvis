"""Git-ignored local SQLite execution state for Handoff Protocol messages."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3


class StateConflictError(ValueError):
    """A message ID was replayed with a different canonical payload."""


@dataclass(frozen=True)
class ExecutionRecord:
    message_id: str; correlation_id: str; source_commit_sha: str; payload_sha256: str
    processing_state: str; attempt_count: int; worktree_path: str | None; branch_name: str | None
    resulting_commit_sha: str | None; test_result_summary: str | None
    started_at: str; finished_at: str | None; error_category: str | None


class StateStore:
    """Small transactional store; callers choose a Git-ignored database path."""

    def __init__(self, path: Path | str) -> None:
        self._memory_connection: sqlite3.Connection | None = None
        if str(path) == ":memory:":
            self._path = None
            self._memory_connection = sqlite3.connect(":memory:")
            self._memory_connection.row_factory = sqlite3.Row
        else:
            self._path = Path(path)
            self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    message_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL, source_commit_sha TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL, processing_state TEXT NOT NULL, attempt_count INTEGER NOT NULL,
                    worktree_path TEXT, branch_name TEXT, resulting_commit_sha TEXT, test_result_summary TEXT,
                    started_at TEXT NOT NULL, finished_at TEXT, error_category TEXT
                )
            """)

    def register(self, *, message_id: str, correlation_id: str, source_commit_sha: str, payload_sha256: str) -> tuple[ExecutionRecord, bool]:
        """Atomically record a request; return (record, exact_replay)."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM executions WHERE message_id = ?", (message_id,)).fetchone()
            if row:
                record = _record(row)
                if record.payload_sha256 != payload_sha256:
                    raise StateConflictError("Message ID conflicts with a different payload.")
                return record, True
            started_at = datetime.now(UTC).isoformat()
            connection.execute("""
                INSERT INTO executions (message_id, correlation_id, source_commit_sha, payload_sha256, processing_state, attempt_count, started_at)
                VALUES (?, ?, ?, ?, 'accepted', 0, ?)
            """, (message_id, correlation_id, source_commit_sha, payload_sha256, started_at))
            row = connection.execute("SELECT * FROM executions WHERE message_id = ?", (message_id,)).fetchone()
            return _record(row), False

    def update(self, message_id: str, *, processing_state: str, attempt_count: int | None = None, worktree_path: str | None = None, branch_name: str | None = None, resulting_commit_sha: str | None = None, test_result_summary: str | None = None, finished: bool = False, error_category: str | None = None) -> ExecutionRecord:
        """Update only explicit fields; later policy tasks constrain valid transitions."""
        assignments, values = ["processing_state = ?"], [processing_state]
        for column, value in (("attempt_count", attempt_count), ("worktree_path", worktree_path), ("branch_name", branch_name), ("resulting_commit_sha", resulting_commit_sha), ("test_result_summary", test_result_summary), ("error_category", error_category)):
            if value is not None: assignments.append(f"{column} = ?"); values.append(value)
        if finished: assignments.append("finished_at = ?"); values.append(datetime.now(UTC).isoformat())
        values.append(message_id)
        with self._connect() as connection:
            result = connection.execute(f"UPDATE executions SET {', '.join(assignments)} WHERE message_id = ?", values)
            if result.rowcount != 1: raise KeyError(message_id)
            return _record(connection.execute("SELECT * FROM executions WHERE message_id = ?", (message_id,)).fetchone())

    def get(self, message_id: str) -> ExecutionRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM executions WHERE message_id = ?", (message_id,)).fetchone()
            return _record(row) if row else None

    def unfinished(self) -> tuple[ExecutionRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM executions WHERE finished_at IS NULL ORDER BY started_at").fetchall()
            return tuple(_record(row) for row in rows)

    def _connect(self) -> sqlite3.Connection:
        if self._memory_connection is not None:
            return self._memory_connection
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection


def _record(row: sqlite3.Row) -> ExecutionRecord:
    return ExecutionRecord(**dict(row))
