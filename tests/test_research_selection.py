import unittest
from uuid import UUID
from datetime import datetime, UTC

from pydantic import ValidationError

from jarvis.integrations.mitir.models import ResearchSelectCandidatesInput, TaskRequest
from jarvis.research_proposal import ProposalState, ResearchActionProposal
from jarvis.research_selection import ResearchSelectionWaiting, present_waiting_for_approval


class ResearchSelectionContractTests(unittest.TestCase):
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

    def test_waiting_presentation_stops_at_mitir_confirmation(self):
        text = present_waiting_for_approval(ResearchSelectionWaiting("proposal", "task", "22222222-2222-4222-8222-222222222222", "2026-08-16T00:00:00+00:00", "await_mitir_confirmation_contract"))
        self.assertIn("waiting for MiTiR confirmation", text)
        self.assertIn("await_mitir_confirmation_contract", text)
        self.assertNotIn("Bearer", text)
