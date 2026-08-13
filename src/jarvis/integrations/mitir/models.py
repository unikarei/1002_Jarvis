"""Typed models mirroring MiTiR Integration API v0.1.0."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


API_VERSION = "0.1.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Health(StrictModel):
    status: Literal["ok"]
    component: Literal["secretary"]
    api_version: Literal["0.1.0"]
    ready: bool


class Capability(StrictModel):
    id: Literal["daily.summary", "research.summary", "trading.context"]
    description: str
    version: str
    available: bool
    approval_required: bool
    input_schema: str
    output_schema: str


class CapabilityList(StrictModel):
    api_version: Literal["0.1.0"]
    capabilities: list[Capability]


class TaskState(StrEnum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


class TaskRequest(StrictModel):
    capability_id: Literal["daily.summary", "research.summary", "trading.context"]
    input: dict[str, Any]
    correlation_id: str | None = Field(default=None, max_length=200)
    requester: str | None = Field(default=None, max_length=200)


class TaskError(StrictModel):
    code: str
    message: str
    retryable: bool
    task_id: str | None = None
    correlation_id: str | None = None


class ErrorEnvelope(StrictModel):
    error: TaskError


class TaskRecord(StrictModel):
    id: UUID
    capability_id: str
    state: TaskState
    correlation_id: str | None = None
    requester: str | None = None
    result: dict[str, Any] | None = None
    error: TaskError | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

