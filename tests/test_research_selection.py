import unittest
from uuid import UUID

from pydantic import ValidationError

from jarvis.integrations.mitir.models import ResearchSelectCandidatesInput, TaskRequest
from jarvis.research_proposal import ProposalState, ResearchActionProposal


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
