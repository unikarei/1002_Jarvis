"""Tests for the local-only Research proposal gate."""

import unittest
from datetime import UTC, datetime, timedelta

from jarvis.research_proposal import InMemoryProposalStore, ProposalError, ProposalState, ResearchProposalService


class ResearchProposalTests(unittest.TestCase):
    def test_proposal_is_bounded_and_starts_without_a_remote_side_effect(self):
        service = ResearchProposalService()
        proposal = service.propose("Start Research on battery recycling")
        self.assertEqual(proposal.state, ProposalState.PROPOSED)
        self.assertEqual(proposal.target, "battery recycling")
        self.assertLessEqual(len(proposal.intent_summary), 280)

    def test_approval_is_separate_idempotent_and_stops_at_contract_gate(self):
        service = ResearchProposalService()
        proposal = service.propose("Start Research on batteries")
        first = service.approve(proposal.proposal_id)
        self.assertEqual(first.state, ProposalState.APPROVED_PENDING_REMOTE_CONTRACT)
        self.assertEqual(service.approve(proposal.proposal_id), first)

    def test_reject_unknown_and_multiple_pending_are_safe(self):
        service = ResearchProposalService()
        first, second = service.propose("Start Research on one"), service.propose("Start Research on two")
        with self.assertRaises(ProposalError): service.approve(None)
        self.assertEqual(service.reject(first.proposal_id).state, ProposalState.REJECTED)
        with self.assertRaises(ProposalError): service.approve(first.proposal_id)
        with self.assertRaises(ProposalError): service.approve("unknown")
        self.assertEqual(second.state, ProposalState.PROPOSED)

    def test_expired_proposal_cannot_be_approved(self):
        current = [datetime(2026, 1, 1, tzinfo=UTC)]
        store = InMemoryProposalStore(clock=lambda: current[0])
        service = ResearchProposalService(store)
        proposal = service.propose("Start Research on batteries")
        current[0] += timedelta(minutes=16)
        self.assertEqual(store.get(proposal.proposal_id).state, ProposalState.EXPIRED)
        with self.assertRaises(ProposalError): service.approve(proposal.proposal_id)
