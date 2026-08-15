"""JARVIS-local, human-approved Research proposal lifecycle (no remote transport)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4


class ProposalState(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    APPROVED_PENDING_REMOTE_CONTRACT = "approved_pending_remote_contract"
    SUBMITTED = "submitted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProposalError(ValueError):
    """A safe local proposal lifecycle error."""


@dataclass(frozen=True)
class ResearchActionProposal:
    proposal_id: str
    action_type: str
    title: str
    intent_summary: str
    target: str | None
    options: tuple[str, ...]
    expected_effect: str
    mitir_additional_approval_may_be_required: bool
    created_at: datetime
    state: ProposalState


class InMemoryProposalStore:
    """Application-lifetime store for the current CLI/session architecture."""

    def __init__(self, *, clock: callable = lambda: datetime.now(UTC), ttl: timedelta = timedelta(minutes=15)) -> None:
        self._clock, self._ttl, self._proposals = clock, ttl, {}

    def add(self, proposal: ResearchActionProposal) -> ResearchActionProposal:
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def now(self) -> datetime:
        return self._clock()

    def get(self, proposal_id: str) -> ResearchActionProposal:
        try:
            proposal = self._proposals[proposal_id]
        except KeyError as exc:
            raise ProposalError("Unknown proposal ID.") from exc
        if proposal.state is ProposalState.PROPOSED and self._clock() - proposal.created_at >= self._ttl:
            proposal = self._set(proposal, ProposalState.EXPIRED)
        return proposal

    def pending(self) -> tuple[ResearchActionProposal, ...]:
        return tuple(proposal for proposal in self._proposals.values() if self.get(proposal.proposal_id).state is ProposalState.PROPOSED)

    def transition(self, proposal_id: str, expected: ProposalState, target: ProposalState) -> ResearchActionProposal:
        proposal = self.get(proposal_id)
        if proposal.state is not expected:
            raise ProposalError(f"Proposal is {proposal.state}; cannot transition to {target}.")
        return self._set(proposal, target)

    def _set(self, proposal: ResearchActionProposal, state: ProposalState) -> ResearchActionProposal:
        updated = replace(proposal, state=state)
        self._proposals[proposal.proposal_id] = updated
        return updated


class ResearchProposalService:
    """Constructs and approves local proposals; intentionally has no MiTiR client."""

    def __init__(self, store: InMemoryProposalStore | None = None) -> None:
        self._store = store or InMemoryProposalStore()

    def propose(self, user_message: str) -> ResearchActionProposal:
        summary = _bounded(user_message)
        target = _target_from(summary)
        return self._store.add(ResearchActionProposal(
            proposal_id=str(uuid4()), action_type="research_action", title="Research action proposal",
            intent_summary=summary, target=target, options=(),
            expected_effect="Request bounded Research work after separate human approval and a supported external contract.",
            mitir_additional_approval_may_be_required=True, created_at=self._store.now(), state=ProposalState.PROPOSED,
        ))

    def approve(self, proposal_id: str | None) -> ResearchActionProposal:
        proposal = self._resolve_pending(proposal_id)
        if proposal.state is ProposalState.APPROVED_PENDING_REMOTE_CONTRACT:
            return proposal
        self._store.transition(proposal.proposal_id, ProposalState.PROPOSED, ProposalState.APPROVED)
        return self._store.transition(proposal.proposal_id, ProposalState.APPROVED, ProposalState.APPROVED_PENDING_REMOTE_CONTRACT)

    def reject(self, proposal_id: str | None) -> ResearchActionProposal:
        proposal = self._resolve_pending(proposal_id)
        return self._store.transition(proposal.proposal_id, ProposalState.PROPOSED, ProposalState.REJECTED)

    def _resolve_pending(self, proposal_id: str | None) -> ResearchActionProposal:
        if proposal_id:
            proposal = self._store.get(proposal_id)
            if proposal.state is ProposalState.APPROVED_PENDING_REMOTE_CONTRACT:
                return proposal
            if proposal.state is not ProposalState.PROPOSED:
                raise ProposalError(f"Proposal is {proposal.state}; it cannot be decided.")
            return proposal
        pending = self._store.pending()
        if len(pending) != 1:
            raise ProposalError("Specify a proposal ID; there is not exactly one pending proposal.")
        return pending[0]


def present_proposal(proposal: ResearchActionProposal) -> str:
    lines = ["Research action proposal", f"Proposal ID: {proposal.proposal_id}", f"Intent: {proposal.intent_summary}"]
    if proposal.target:
        lines.append(f"Target: {proposal.target}")
    lines.extend([f"Expected effect: {proposal.expected_effect}", "No remote action has been requested.", f"Reply `approve {proposal.proposal_id}` or `reject {proposal.proposal_id}`."])
    return "\n".join(lines)


def _bounded(value: str) -> str:
    return " ".join(value.split())[:280]


def _target_from(summary: str) -> str | None:
    marker = " on "
    return _bounded(summary.split(marker, 1)[1]) if marker in summary else None
