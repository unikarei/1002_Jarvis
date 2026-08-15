"""JARVIS-owned daily-summary application use case built on ``MiTiRClient``."""

from __future__ import annotations

import time
from os import environ
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4

from .errors import MiTiRAPIError, MiTiRContractError, MiTiRTransportError
from .client import MiTiRClient
from .models import TaskRecord, TaskRequest, TaskState


class DailySummaryFailureCategory(StrEnum):
    CONFIGURATION = "configuration_error"
    UNREACHABLE = "unreachable"
    NOT_READY = "not_ready"
    UNAUTHORIZED = "unauthorized"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    TIMEOUT = "timeout"
    TASK_FAILED = "task_failed"
    CONTRACT = "contract_error"


class DailySummaryError(Exception):
    """Safe, stable failure exposed by the JARVIS daily-summary boundary."""

    def __init__(
        self,
        category: DailySummaryFailureCategory,
        message: str,
        *,
        task_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.task_id = task_id
        self.correlation_id = correlation_id


@dataclass(frozen=True)
class DailySummaryResult:
    """Stable JARVIS representation of an available MiTiR Daily Intelligence result."""

    status: str | None
    reporting_at: str | None
    headline: str | None
    important_items: tuple[object, ...]
    alerts: tuple[object, ...]
    source_references: tuple[object, ...]
    task_id: str
    correlation_id: str
    terminal_state: str
    completed_at: str | None


class DailySummaryClient(Protocol):
    def get_health(self): ...
    def list_capabilities(self): ...
    def create_task(self, task: TaskRequest, *, idempotency_key: str) -> TaskRecord: ...
    def get_task(self, task_id: str) -> TaskRecord: ...


class DailySummaryService:
    """Hides MiTiR endpoints and task polling from JARVIS product callers."""

    def __init__(
        self,
        client: DailySummaryClient,
        *,
        max_attempts: int = 12,
        poll_interval: float = 2.0,
        sleep=time.sleep,
    ) -> None:
        if max_attempts < 1 or poll_interval < 0:
            raise ValueError("max_attempts must be at least 1 and poll_interval non-negative")
        self._client = client
        self._max_attempts = max_attempts
        self._poll_interval = poll_interval
        self._sleep = sleep

    def get_daily_summary(self) -> DailySummaryResult:
        correlation_id = f"jarvis-daily-summary-{uuid4()}"
        try:
            health = self._client.get_health()
            if not health.ready:
                raise DailySummaryError(DailySummaryFailureCategory.NOT_READY, "MiTiR is not ready")
            capabilities = self._client.list_capabilities()
            if not any(item.id == "daily.summary" and item.available for item in capabilities.capabilities):
                raise DailySummaryError(
                    DailySummaryFailureCategory.CAPABILITY_UNAVAILABLE,
                    "MiTiR Daily Summary is unavailable",
                )
            task = self._client.create_task(
                TaskRequest(
                    capability_id="daily.summary", input={}, correlation_id=correlation_id,
                    requester="jarvis",
                ),
                idempotency_key=f"jarvis-daily-summary-{uuid4()}",
            )
        except DailySummaryError:
            raise
        except MiTiRAPIError as exc:
            raise self._map_api_error(exc, correlation_id) from exc
        except MiTiRContractError as exc:
            raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR returned an invalid response") from exc
        except MiTiRTransportError as exc:
            raise DailySummaryError(DailySummaryFailureCategory.UNREACHABLE, "MiTiR is unreachable") from exc

        for _ in range(self._max_attempts):
            if task.state in {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}:
                break
            self._sleep(self._poll_interval)
            try:
                task = self._client.get_task(str(task.id))
            except MiTiRAPIError as exc:
                raise self._map_api_error(exc, correlation_id) from exc
            except MiTiRContractError as exc:
                raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR returned an invalid response") from exc
            except MiTiRTransportError as exc:
                raise DailySummaryError(DailySummaryFailureCategory.UNREACHABLE, "MiTiR is unreachable") from exc
        else:
            raise DailySummaryError(
                DailySummaryFailureCategory.TIMEOUT, "MiTiR Daily Summary timed out",
                task_id=str(task.id), correlation_id=correlation_id,
            )

        if task.state is not TaskState.SUCCEEDED:
            raise DailySummaryError(
                DailySummaryFailureCategory.TASK_FAILED, "MiTiR Daily Summary did not succeed",
                task_id=str(task.id), correlation_id=correlation_id,
            )
        if task.correlation_id != correlation_id or task.result is None:
            raise DailySummaryError(
                DailySummaryFailureCategory.CONTRACT, "MiTiR Daily Summary response was incomplete",
                task_id=str(task.id), correlation_id=correlation_id,
            )
        return map_daily_summary_result(task, correlation_id)

    @staticmethod
    def _map_api_error(exc: MiTiRAPIError, correlation_id: str) -> DailySummaryError:
        category = (
            DailySummaryFailureCategory.UNAUTHORIZED if exc.status_code == 401
            else DailySummaryFailureCategory.CAPABILITY_UNAVAILABLE
            if exc.error.code == "unsupported_capability"
            else DailySummaryFailureCategory.CONTRACT
        )
        message = (
            "MiTiR authorization failed" if category is DailySummaryFailureCategory.UNAUTHORIZED
            else "MiTiR Daily Summary is unavailable" if category is DailySummaryFailureCategory.CAPABILITY_UNAVAILABLE
            else "MiTiR rejected the request"
        )
        return DailySummaryError(category, message, task_id=exc.error.task_id, correlation_id=exc.error.correlation_id or correlation_id)


def daily_summary_service_from_environment(
    environment: dict[str, str] | None = None,
    **service_options: Any,
) -> DailySummaryService:
    """Compose the use case from runtime-only configuration without exposing values."""
    runtime = environ if environment is None else environment
    base_url = runtime.get("MITIR_BASE_URL")
    token = runtime.get("MITIR_INTEGRATION_TOKEN")
    if not base_url or not token:
        raise DailySummaryError(
            DailySummaryFailureCategory.CONFIGURATION,
            "MiTiR runtime configuration is missing",
        )
    try:
        return DailySummaryService(MiTiRClient(base_url, token), **service_options)
    except ValueError as exc:
        raise DailySummaryError(
            DailySummaryFailureCategory.CONFIGURATION,
            "MiTiR runtime configuration is invalid",
        ) from exc


def map_daily_summary_result(task: TaskRecord, correlation_id: str) -> DailySummaryResult:
    """Map known optional MiTiR domain-summary fields without fabricating missing values."""
    if not isinstance(task.result, dict):
        raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR Daily Summary result was invalid")
    result = task.result
    return DailySummaryResult(
        status=_optional_text(result, "status"),
        reporting_at=_optional_text(result, "reporting_at"),
        headline=_optional_text(result, "headline"),
        important_items=_optional_sequence(result, "important_items"),
        alerts=_optional_sequence(result, "alerts"),
        source_references=_optional_sequence(result, "source_artifacts"),
        task_id=str(task.id), correlation_id=correlation_id, terminal_state=task.state.value,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


def _optional_text(result: dict[str, Any], field: str) -> str | None:
    value = result.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR Daily Summary result was invalid")
    return value


def _optional_sequence(result: dict[str, Any], field: str) -> tuple[object, ...]:
    value = result.get(field)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise DailySummaryError(DailySummaryFailureCategory.CONTRACT, "MiTiR Daily Summary result was invalid")
    return tuple(value)
