"""v0.2.0 bounded Research selection adapter; no confirmation/resume operation exists."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
from .integrations.mitir.models import ResearchSelectCandidatesInput, TaskRequest, TaskState, WaitingForApprovalResult
from .research_proposal import ProposalError, ProposalState, ResearchActionProposal

@dataclass(frozen=True)
class ResearchSelectionWaiting:
    proposal_id: str; task_id: str; mitir_confirmation_id: str; expires_at: str; next_action: str

class ResearchSelectionService:
    """Uses only the documented typed task client and stops at MiTiR confirmation."""
    def __init__(self, client) -> None: self._client = client
    def submit(self, proposal: ResearchActionProposal, *, approval_reference: str, candidate_ids: list[str]) -> ResearchSelectionWaiting:
        if proposal.state is not ProposalState.APPROVED_PENDING_REMOTE_CONTRACT:
            raise ProposalError("Only an approved pending-contract proposal is submission-ready.")
        payload = ResearchSelectCandidatesInput(proposal_id=proposal.proposal_id, approval_reference=approval_reference, candidate_ids=candidate_ids)
        task = self._client.create_task(TaskRequest(capability_id="research.select_candidates", input=payload.model_dump(mode="json"), correlation_id=f"jarvis-research-select-{uuid4()}", requester="jarvis"), idempotency_key=f"jarvis-research-select-{proposal.proposal_id}")
        if task.state is not TaskState.WAITING_FOR_APPROVAL or task.result is None:
            raise ProposalError("MiTiR did not return the required waiting_for_approval state.")
        waiting = WaitingForApprovalResult.model_validate(task.result)
        return ResearchSelectionWaiting(str(waiting.proposal_id), str(task.id), str(waiting.mitir_confirmation_id), waiting.expires_at.isoformat(), waiting.next_action)
