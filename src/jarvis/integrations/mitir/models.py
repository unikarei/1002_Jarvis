"""Typed models mirroring MiTiR Integration API v0.2.0."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


API_VERSION = "0.2.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Health(StrictModel):
    status: Literal["ok"]
    component: Literal["secretary"]
    api_version: Literal["0.1.0", "0.2.0"]
    ready: bool


class Capability(StrictModel):
    id: Literal["daily.summary", "research.summary", "trading.context", "research.select_candidates"]
    description: str
    version: str
    available: bool
    approval_required: bool
    input_schema: str
    output_schema: str


class CapabilityList(StrictModel):
    api_version: Literal["0.1.0", "0.2.0"]
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
    capability_id: Literal["daily.summary", "research.summary", "trading.context", "research.select_candidates"]
    input: dict[str, Any]
    correlation_id: str | None = Field(default=None, max_length=200)
    requester: str | None = Field(default=None, max_length=200)

    def model_post_init(self, __context: Any) -> None:
        if self.capability_id == "research.select_candidates":
            ResearchSelectCandidatesInput.model_validate(self.input)


class ResearchSelectCandidatesInput(StrictModel):
    proposal_id: UUID
    approval_reference: str = Field(min_length=1, max_length=200)
    candidate_ids: list[str] = Field(min_length=1, max_length=20)

    def model_post_init(self, __context: Any) -> None:
        if any(not candidate_id or len(candidate_id) > 200 for candidate_id in self.candidate_ids):
            raise ValueError("candidate_ids must be non-empty and at most 200 characters")
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("candidate_ids must be unique")


class WaitingForApprovalResult(StrictModel):
    status: Literal["waiting_for_approval"]
    proposal_id: UUID
    candidate_ids: list[str]
    mitir_confirmation_id: UUID
    expires_at: datetime
    next_action: Literal["await_mitir_confirmation_contract"]


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
