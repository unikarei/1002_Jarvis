import unittest
from uuid import UUID
from datetime import datetime, UTC

from pydantic import ValidationError

from jarvis.integrations.mitir.errors import MiTiRContractError
from jarvis.integrations.mitir.models import ResearchSelectCandidatesInput, TaskRecord, TaskRequest, WaitingForApprovalResult
from jarvis.research_proposal import ProposalState, ResearchActionProposal, ResearchProposalService
from jarvis.research_selection import ResearchSelectionService, ResearchSelectionWaiting, present_waiting_for_approval


class ResearchSelectionContractTests(unittest.TestCase):
    def _waiting_task(self, proposal_id):
        return TaskRecord.model_validate({"id": "33333333-3333-4333-8333-333333333333", "capability_id": "research.select_candidates", "state": "waiting_for_approval", "correlation_id": "corr", "requester": "jarvis", "result": {"status": "waiting_for_approval", "proposal_id": proposal_id, "candidate_ids": ["candidate-1"], "mitir_confirmation_id": "22222222-2222-4222-8222-222222222222", "expires_at": "2026-08-16T00:00:00Z", "next_action": "await_mitir_confirmation_contract"}, "error": None, "created_at": "2026-08-16T00:00:00Z", "updated_at": "2026-08-16T00:00:00Z", "started_at": "2026-08-16T00:00:00Z", "completed_at": None})
    def test_closed_input_accepts_only_bounded_unique_candidates(self):
        payload = ResearchSelectCandidatesInput(proposal_id="11111111-1111-4111-8111-111111111111", approval_reference="gate-a-approved", candidate_ids=["candidate-1"])
        self.assertEqual(payload.candidate_ids, ["candidate-1"])
        with self.assertRaises(ValidationError):
            ResearchSelectCandidatesInput(proposal_id="11111111-1111-4111-8111-111111111111", approval_reference="ok", candidate_ids=["same", "same"])
        with self.assertRaises(ValidationError):
            ResearchSelectCandidatesInput(proposal_id="11111111-1111-4111-8111-111111111111", approval_reference="ok", candidate_ids=[])
        with self.assertRaises(ValidationError):
            ResearchSelectCandidatesInput(proposal_id="11111111-1111-4111-8111-111111111111", approval_reference="ok", candidate_ids=["one"], unexpected="value")

    def test_task_request_rejects_invalid_selection_before_transport(self):
        with self.assertRaises(ValidationError):
            TaskRequest(capability_id="research.select_candidates", input={})

    def test_waiting_result_rejects_invalid_candidate_ids(self):
        base = {"status": "waiting_for_approval", "proposal_id": "11111111-1111-4111-8111-111111111111", "candidate_ids": ["candidate-1"], "mitir_confirmation_id": "22222222-2222-4222-8222-222222222222", "expires_at": "2026-08-16T00:00:00Z", "next_action": "await_mitir_confirmation_contract"}
        for candidate_ids in ([], ["same", "same"], [""], ["x" * 201]):
            with self.subTest(candidate_ids=candidate_ids), self.assertRaises(ValidationError):
                WaitingForApprovalResult.model_validate({**base, "candidate_ids": candidate_ids})

    def test_waiting_presentation_stops_at_mitir_confirmation(self):
        text = present_waiting_for_approval(ResearchSelectionWaiting("proposal", "task", "22222222-2222-4222-8222-222222222222", "2026-08-16T00:00:00+00:00", "await_mitir_confirmation_contract"))
        self.assertIn("waiting for MiTiR confirmation", text)
        self.assertIn("await_mitir_confirmation_contract", text)
        self.assertNotIn("Bearer", text)

    def test_mocked_submission_is_idempotent_at_the_proposal_boundary(self):
        class FakeClient:
            def __init__(self, task): self.task, self.calls, self.keys = task, 0, []
            def create_task(self, request, *, idempotency_key): self.calls += 1; self.keys.append(idempotency_key); return self.task
        lifecycle = ResearchProposalService()
        proposal = lifecycle.propose("Start Research on batteries")
        proposal = lifecycle.approve(proposal.proposal_id)
        client = FakeClient(self._waiting_task(proposal.proposal_id))
        result = ResearchSelectionService(client).submit(proposal, approval_reference="gate-a-approved", candidate_ids=["candidate-1"], lifecycle=lifecycle)
        self.assertEqual(result.next_action, "await_mitir_confirmation_contract")
        self.assertEqual(client.calls, 1)
        self.assertEqual(lifecycle._store.get(proposal.proposal_id).state, ProposalState.WAITING_FOR_APPROVAL)
        with self.assertRaises(Exception):
            ResearchSelectionService(client).submit(lifecycle._store.get(proposal.proposal_id), approval_reference="gate-a-approved", candidate_ids=["candidate-1"], lifecycle=lifecycle)
        self.assertEqual(client.calls, 1)

    def test_waiting_task_cancellation_uses_only_the_published_cancel_route(self):
        class FakeClient:
            def __init__(self, task): self.task, self.cancelled = task, []
            def create_task(self, request, *, idempotency_key): return self.task
            def cancel_task(self, task_id):
                self.cancelled.append(task_id)
                return TaskRecord.model_validate({**self.task.model_dump(mode="json"), "state": "cancelled"})
        lifecycle = ResearchProposalService()
        proposal = lifecycle.approve(lifecycle.propose("Start Research on batteries").proposal_id)
        client = FakeClient(self._waiting_task(proposal.proposal_id))
        service = ResearchSelectionService(client)
        waiting = service.submit(proposal, approval_reference="gate-a-approved", candidate_ids=["candidate-1"], lifecycle=lifecycle)
        self.assertEqual(service.cancel_waiting(waiting, lifecycle=lifecycle).state, ProposalState.CANCELLED)
        self.assertEqual(client.cancelled, [waiting.task_id])

    def test_misbound_waiting_result_does_not_advance_proposal_lifecycle(self):
        class FakeClient:
            def __init__(self, task): self.task = task
            def create_task(self, request, *, idempotency_key): return self.task
        for result_change in ({"proposal_id": "44444444-4444-4444-8444-444444444444"}, {"candidate_ids": ["candidate-2"]}):
            with self.subTest(result_change=result_change):
                lifecycle = ResearchProposalService()
                proposal = lifecycle.approve(lifecycle.propose("Start Research on batteries").proposal_id)
                task = self._waiting_task(proposal.proposal_id)
                task = task.model_copy(update={"result": {**task.result, **result_change}})
                with self.assertRaises(MiTiRContractError):
                    ResearchSelectionService(FakeClient(task)).submit(proposal, approval_reference="gate-a-approved", candidate_ids=["candidate-1"], lifecycle=lifecycle)
                self.assertEqual(lifecycle._store.get(proposal.proposal_id).state, ProposalState.APPROVED_PENDING_REMOTE_CONTRACT)
