"""Safe local primitives for the Git Handoff Automation runner."""

from .protocol import HandoffEnvelope, ProtocolError, canonical_payload_sha256, parse_markdown_entry
from .policy import PolicyDecision, PolicyEngine
from .git_transport import GitTransport, GitTransportError, RemoteDocument
from .worktree import TaskWorktree, WorktreeError, WorktreeManager
from .state_store import ExecutionRecord, StateConflictError, StateStore

__all__ = ["ExecutionRecord", "GitTransport", "GitTransportError", "HandoffEnvelope", "PolicyDecision", "PolicyEngine", "ProtocolError", "RemoteDocument", "StateConflictError", "StateStore", "TaskWorktree", "WorktreeError", "WorktreeManager", "canonical_payload_sha256", "parse_markdown_entry"]
