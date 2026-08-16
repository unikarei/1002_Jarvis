"""Initial-release execution policy for validated handoff envelopes."""
from __future__ import annotations

from dataclasses import dataclass

from .protocol import HandoffEnvelope

_LEVEL_ACTIONS = {
    "L0": frozenset({"inspection", "reporting"}),
    "L1": frozenset({"inspection", "reporting", "documentation"}),
    "L2": frozenset({"inspection", "reporting", "source_changes", "tests"}),
}
_ALWAYS_PROHIBITED = frozenset({"trading_mutation", "trading", "live_mitir_mutation", "rm_t10"})


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    status: str
    reason: str


class PolicyEngine:
    """Deny by default; this release permits only local L0–L2 work."""

    def __init__(self, *, agent_execution_enabled: bool = True) -> None:
        self._agent_execution_enabled = agent_execution_enabled

    def evaluate(self, envelope: HandoffEnvelope) -> PolicyDecision:
        prohibited = {_normalize(value) for value in envelope.prohibited_actions}
        if prohibited & _ALWAYS_PROHIBITED:
            return PolicyDecision(False, "rejected", "Trading, RM-T10, and live MiTiR mutation are prohibited.")
        if envelope.execution_level in {"L3", "L4"}:
            return PolicyDecision(False, "rejected", "L3 and L4 are disabled in the initial release.")
        actions = _LEVEL_ACTIONS[envelope.execution_level]
        if prohibited & actions:
            return PolicyDecision(False, "rejected", "Requested level conflicts with prohibited actions.")
        if envelope.requires_approval:
            return PolicyDecision(False, "approval_required", "Explicit human approval is required before execution.")
        if not self._agent_execution_enabled and envelope.execution_level != "L0":
            return PolicyDecision(False, "blocked", "Emergency kill switch disables agent execution.")
        return PolicyDecision(True, "accepted", "Execution level is permitted by initial-release policy.")


def _normalize(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")
