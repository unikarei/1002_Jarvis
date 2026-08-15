"""JARVIS-owned read-only Research Summary use case."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from typing import Any, Protocol

from .daily_summary import DailySummaryError, DailySummaryFailureCategory
from .client import MiTiRClient
from .models import TaskRecord
from .specialist_read import ReadOnlySpecialistRunner


class ResearchRunner(Protocol):
    def run(self, capability_id: str, payload: dict[str, Any], *, requester: str) -> tuple[TaskRecord, str]: ...


@dataclass(frozen=True)
class ResearchSummaryResult:
    status: str | None
    reporting_at: str | None
    headline: str | None
    items: tuple[object, ...]
    alerts: tuple[object, ...]
    source_references: tuple[object, ...]
    task_id: str
    correlation_id: str
    terminal_state: str


class ResearchSummaryService:
    def __init__(self, runner: ResearchRunner) -> None:
        self._runner = runner

    def get_summary(self) -> ResearchSummaryResult:
        task, correlation_id = self._runner.run("research.summary", {}, requester="jarvis")
        return map_research_summary_result(task, correlation_id)


def research_summary_service_from_environment(environment: dict[str, str] | None = None) -> ResearchSummaryService:
    runtime = environ if environment is None else environment
    base_url, token = runtime.get("MITIR_BASE_URL"), runtime.get("MITIR_INTEGRATION_TOKEN")
    if not base_url or not token:
        raise DailySummaryError(DailySummaryFailureCategory.CONFIGURATION, "MiTiR runtime configuration is missing")
    try:
        return ResearchSummaryService(ReadOnlySpecialistRunner(MiTiRClient(base_url, token)))
    except ValueError as exc:
        raise DailySummaryError(DailySummaryFailureCategory.CONFIGURATION, "MiTiR runtime configuration is invalid") from exc


def map_research_summary_result(task: TaskRecord, correlation_id: str) -> ResearchSummaryResult:
    if not isinstance(task.result, dict):
        raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR Research result was invalid")
    result = task.result
    return ResearchSummaryResult(
        status=_text(result, "status"), reporting_at=_text(result, "reporting_at"), headline=_text(result, "headline"),
        items=_items(result, "important_items"), alerts=_items(result, "alerts"), source_references=_items(result, "source_artifacts"),
        task_id=str(task.id), correlation_id=correlation_id, terminal_state=task.state.value,
    )


def _text(result: dict[str, Any], field: str) -> str | None:
    value = result.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR Research result was invalid")
    return value


def _items(result: dict[str, Any], field: str) -> tuple[object, ...]:
    value = result.get(field)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR Research result was invalid")
    return tuple(value)
