"""Deterministic conversational intent routing for JARVIS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .integrations.mitir.daily_summary import DailySummaryError, DailySummaryResult
from .integrations.mitir.research_summary import ResearchSummaryResult
from .integrations.mitir.trading_context import TradingContextResult
from .research_proposal import ProposalError, ResearchProposalService, present_proposal


class ConversationIntent(StrEnum):
    DAILY = "daily"
    RESEARCH = "research"
    TRADING = "trading"
    RESEARCH_MUTATION = "research_mutation"
    APPROVE_PROPOSAL = "approve_proposal"
    REJECT_PROPOSAL = "reject_proposal"
    CLARIFY = "clarify"
    UNSUPPORTED = "unsupported"
    READ_ONLY_BOUNDARY = "read_only_boundary"


@dataclass(frozen=True)
class RoutingDecision:
    intent: ConversationIntent
    message: str


@dataclass(frozen=True)
class SecretaryResponse:
    text: str
    domain: ConversationIntent | None = None
    task_id: str | None = None
    correlation_id: str | None = None
    terminal_state: str | None = None


class DailyUseCase(Protocol):
    def get_daily_summary(self) -> DailySummaryResult: ...


class ResearchUseCase(Protocol):
    def get_summary(self) -> ResearchSummaryResult: ...


class TradingUseCase(Protocol):
    def get_context(self) -> TradingContextResult: ...


class IntentRouter:
    """Routes read requests and local Research proposals without API payloads."""

    _MUTATING_TERMS = ("buy", "sell", "order", "trade this", "approve", "start", "create", "delete")
    _DAILY_TERMS = ("daily", "today", "summary")
    _RESEARCH_TERMS = ("research", "study")
    _TRADING_TERMS = ("trading", "trade", "portfolio", "market")
    _RESEARCH_ACTION_TERMS = ("start", "create", "execute", "run", "perform", "prepare", "research this")
    _APPROVE_TERMS = ("approve", "yes", "ok")
    _REJECT_TERMS = ("reject", "cancel", "no")

    def route(self, message: str) -> RoutingDecision:
        normalized = " ".join(message.casefold().split())
        if not normalized:
            return RoutingDecision(ConversationIntent.CLARIFY, "What would you like to see: Daily, Research, or Trading status?")
        has_research = any(term in normalized for term in self._RESEARCH_TERMS)
        has_trading = any(term in normalized for term in self._TRADING_TERMS)
        if has_research and has_trading and any(term in normalized for term in self._MUTATING_TERMS):
            return RoutingDecision(ConversationIntent.CLARIFY, "Please choose either a Research proposal or a Trading status request.")
        if has_trading and any(term in normalized for term in self._MUTATING_TERMS):
            return RoutingDecision(ConversationIntent.READ_ONLY_BOUNDARY, "JARVIS cannot execute or approve Trading actions.")
        if normalized.startswith(self._APPROVE_TERMS):
            return RoutingDecision(ConversationIntent.APPROVE_PROPOSAL, "")
        if normalized.startswith(self._REJECT_TERMS):
            return RoutingDecision(ConversationIntent.REJECT_PROPOSAL, "")
        if has_research and any(term in normalized for term in self._RESEARCH_ACTION_TERMS):
            if has_trading:
                return RoutingDecision(ConversationIntent.CLARIFY, "Please choose either a Research proposal or a Trading status request.")
            return RoutingDecision(ConversationIntent.RESEARCH_MUTATION, "")
        if any(term in normalized for term in self._MUTATING_TERMS):
            return RoutingDecision(ConversationIntent.READ_ONLY_BOUNDARY, "JARVIS is read-only for that request.")

        matches = {
            ConversationIntent.DAILY: any(term in normalized for term in self._DAILY_TERMS),
            ConversationIntent.RESEARCH: has_research,
            ConversationIntent.TRADING: has_trading,
        }
        selected = [intent for intent, matched in matches.items() if matched]
        if len(selected) == 1:
            return RoutingDecision(selected[0], "")
        if len(selected) > 1:
            return RoutingDecision(ConversationIntent.CLARIFY, "Please choose one: Daily, Research, or Trading status.")
        return RoutingDecision(ConversationIntent.UNSUPPORTED, "I can show Daily, Research, or Trading status, or prepare a bounded Research proposal.")


class SecretaryService:
    """Conversation boundary that selects at most one injected read specialist."""

    def __init__(self, daily: DailyUseCase, research: ResearchUseCase, trading: TradingUseCase, *, router: IntentRouter | None = None, proposals: ResearchProposalService | None = None) -> None:
        self._daily, self._research, self._trading = daily, research, trading
        self._router = router or IntentRouter()
        self._proposals = proposals or ResearchProposalService()

    def respond(self, message: str) -> SecretaryResponse:
        decision = self._router.route(message)
        if decision.intent is ConversationIntent.RESEARCH_MUTATION:
            proposal = self._proposals.propose(message)
            return SecretaryResponse(present_proposal(proposal), domain=decision.intent, terminal_state=proposal.state)
        if decision.intent in {ConversationIntent.APPROVE_PROPOSAL, ConversationIntent.REJECT_PROPOSAL}:
            proposal_id = _proposal_id(message)
            try:
                proposal = self._proposals.approve(proposal_id) if decision.intent is ConversationIntent.APPROVE_PROPOSAL else self._proposals.reject(proposal_id)
            except ProposalError as exc:
                return SecretaryResponse(str(exc), domain=decision.intent)
            if decision.intent is ConversationIntent.REJECT_PROPOSAL:
                return SecretaryResponse(f"Research proposal {proposal.proposal_id} rejected. No remote action was requested.", domain=decision.intent, terminal_state=proposal.state)
            return SecretaryResponse(f"Research proposal {proposal.proposal_id} approval is recorded. Remote execution is unavailable until MiTiR publishes a supported external Research mutation contract.", domain=decision.intent, terminal_state=proposal.state)
        if decision.intent not in {ConversationIntent.DAILY, ConversationIntent.RESEARCH, ConversationIntent.TRADING}:
            return SecretaryResponse(decision.message, domain=decision.intent)
        try:
            result = (
                self._daily.get_daily_summary() if decision.intent is ConversationIntent.DAILY
                else self._research.get_summary() if decision.intent is ConversationIntent.RESEARCH
                else self._trading.get_context()
            )
        except DailySummaryError as exc:
            return SecretaryResponse(f"I could not retrieve {decision.intent} status [{exc.category}].", domain=decision.intent, task_id=exc.task_id, correlation_id=exc.correlation_id)
        return _compose_response(decision.intent, result)


def _compose_response(intent: ConversationIntent, result: DailySummaryResult | ResearchSummaryResult | TradingContextResult) -> SecretaryResponse:
    title = {ConversationIntent.DAILY: "Daily Intelligence", ConversationIntent.RESEARCH: "Research status", ConversationIntent.TRADING: "Trading context"}[intent]
    lines = [title]
    reporting_at, status, headline = result.reporting_at, result.status, result.headline
    if reporting_at:
        lines.append(f"Reported: {reporting_at}")
    if status:
        lines.append(f"Status: {status}")
    if getattr(result, "mode", None):
        lines.append(f"Mode: {result.mode} (read-only context)")
    if headline:
        lines.extend(["", headline])
    values = result.important_items if intent is ConversationIntent.DAILY else result.items if intent is ConversationIntent.RESEARCH else result.activity
    _section(lines, "Items", values)
    _section(lines, "Alerts", result.alerts)
    _section(lines, "Sources", result.source_references)
    return SecretaryResponse("\n".join(lines), domain=intent, task_id=result.task_id, correlation_id=result.correlation_id, terminal_state=result.terminal_state)


def _section(lines: list[str], title: str, values: tuple[object, ...]) -> None:
    if values:
        lines.extend(["", f"{title}:"])
        lines.extend(f"- {_item(value)}" for value in values)


def _item(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("title", "headline", "summary", "text"):
            if isinstance(value.get(key), str):
                return value[key]
    return str(value)


def _proposal_id(message: str) -> str | None:
    parts = message.split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else None
