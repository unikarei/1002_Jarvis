"""Deterministic, read-only conversational intent routing for JARVIS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .integrations.mitir.daily_summary import DailySummaryError, DailySummaryResult
from .integrations.mitir.research_summary import ResearchSummaryResult
from .integrations.mitir.trading_context import TradingContextResult


class ConversationIntent(StrEnum):
    DAILY = "daily"
    RESEARCH = "research"
    TRADING = "trading"
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
    """Routes only documented read capabilities; it never emits API details or payloads."""

    _MUTATING_TERMS = (
        "buy", "sell", "order", "trade this", "approve", "start", "create", "delete",
        "買", "売", "注文", "発注", "承認", "開始", "作成", "削除",
    )
    _DAILY_TERMS = ("daily", "today", "今日", "日次", "サマリー")
    _RESEARCH_TERMS = ("research", "study", "研究", "リサーチ")
    _TRADING_TERMS = ("trading", "trade", "portfolio", "market", "取引", "トレード", "ポートフォリオ")

    def route(self, message: str) -> RoutingDecision:
        normalized = " ".join(message.casefold().split())
        if not normalized:
            return RoutingDecision(ConversationIntent.CLARIFY, "What would you like to see: Daily, Research, or Trading status?")
        if any(term in normalized for term in self._MUTATING_TERMS):
            return RoutingDecision(
                ConversationIntent.READ_ONLY_BOUNDARY,
                "JARVIS is read-only in this phase and cannot execute or approve that request.",
            )
        matches = {
            ConversationIntent.DAILY: any(term in normalized for term in self._DAILY_TERMS),
            ConversationIntent.RESEARCH: any(term in normalized for term in self._RESEARCH_TERMS),
            ConversationIntent.TRADING: any(term in normalized for term in self._TRADING_TERMS),
        }
        selected = [intent for intent, matched in matches.items() if matched]
        if len(selected) == 1:
            return RoutingDecision(selected[0], "")
        if len(selected) > 1:
            return RoutingDecision(ConversationIntent.CLARIFY, "Please choose one: Daily, Research, or Trading status.")
        return RoutingDecision(
            ConversationIntent.UNSUPPORTED,
            "I can show read-only Daily, Research, or Trading status.",
        )


class SecretaryService:
    """Conversation boundary that selects at most one injected read-only specialist."""

    def __init__(self, daily: DailyUseCase, research: ResearchUseCase, trading: TradingUseCase, *, router: IntentRouter | None = None) -> None:
        self._daily, self._research, self._trading = daily, research, trading
        self._router = router or IntentRouter()

    def respond(self, message: str) -> SecretaryResponse:
        decision = self._router.route(message)
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
    if reporting_at: lines.append(f"Reported: {reporting_at}")
    if status: lines.append(f"Status: {status}")
    if getattr(result, "mode", None): lines.append(f"Mode: {result.mode} (read-only context)")
    if headline: lines.extend(["", headline])
    values = (
        result.important_items if intent is ConversationIntent.DAILY
        else result.items if intent is ConversationIntent.RESEARCH
        else result.activity
    )
    _section(lines, "Items", values)
    _section(lines, "Alerts", result.alerts)
    _section(lines, "Sources", result.source_references)
    return SecretaryResponse("\n".join(lines), domain=intent, task_id=result.task_id, correlation_id=result.correlation_id, terminal_state=result.terminal_state)


def _section(lines: list[str], title: str, values: tuple[object, ...]) -> None:
    if values:
        lines.extend(["", f"{title}:"])
        lines.extend(f"- {_item(value)}" for value in values)


def _item(value: object) -> str:
    if isinstance(value, str): return value
    if isinstance(value, dict):
        for key in ("title", "headline", "summary", "text"):
            if isinstance(value.get(key), str): return value[key]
    return str(value)
