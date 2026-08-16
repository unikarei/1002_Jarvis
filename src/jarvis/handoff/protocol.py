"""Protocol v1.0.0 parser with no Git, agent, or external side effects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import re
from typing import Any, Mapping
from uuid import UUID

import yaml

PROTOCOL_VERSION = "1.0.0"
TYPES = frozenset({"implementation_request", "documentation_request", "review_request", "status_response", "result_response", "approval_request", "approval_response", "cancellation_request", "error_response"})
STATES = frozenset({"requested", "accepted", "in_progress", "blocked", "approval_required", "completed", "failed", "cancelled", "rejected"})
LEVELS = frozenset({"L0", "L1", "L2", "L3", "L4"})
FIELDS = frozenset({"protocol_version", "message_id", "correlation_id", "created_at", "sender", "recipient", "type", "status", "reply_to", "execution_level", "requires_approval", "expires_at", "max_hops", "payload", "prohibited_actions", "artifacts"})
REQUESTS = frozenset({"implementation_request", "documentation_request", "review_request"})
PAYLOAD_FIELDS = {
    "implementation_request": ({"task_id", "title", "scope"}, {"instructions", "required_tests"}),
    "documentation_request": ({"task_id", "title", "scope"}, {"instructions", "required_tests"}),
    "review_request": ({"task_id", "subject"}, {"files"}),
    "status_response": ({"summary"}, set()), "result_response": ({"summary", "test_summary"}, set()),
    "approval_request": ({"subject", "reason"}, set()), "approval_response": ({"decision"}, {"approval_reference"}),
    "cancellation_request": ({"reason"}, set()), "error_response": ({"category", "summary"}, set()),
}


class ProtocolError(ValueError):
    """A safe protocol-validation error."""


@dataclass(frozen=True)
class HandoffEnvelope:
    message_id: str; correlation_id: str; created_at: datetime; sender: str; recipient: str
    type: str; status: str; reply_to: str | None; execution_level: str; requires_approval: bool
    expires_at: datetime; max_hops: int; payload: Mapping[str, Any]
    prohibited_actions: tuple[str, ...]; artifacts: tuple[Mapping[str, str], ...]


def canonical_payload_sha256(payload: Mapping[str, Any]) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProtocolError("Payload is not canonical JSON.") from exc
    return sha256(text.encode("utf-8")).hexdigest()


def parse_markdown_entry(markdown: str, *, recipient: str, now: datetime | None = None) -> HandoffEnvelope:
    if recipient not in {"jarvis", "mitir"}:
        raise ValueError("Recipient must be jarvis or mitir.")
    blocks = re.findall(r"```ya?ml\s*\n(.*?)```", markdown, flags=re.DOTALL | re.IGNORECASE)
    if len(blocks) != 1:
        raise ProtocolError("A handoff entry must contain exactly one YAML envelope.")
    try:
        raw = yaml.safe_load(blocks[0])
    except yaml.YAMLError as exc:
        raise ProtocolError("Envelope YAML is malformed.") from exc
    if not isinstance(raw, dict):
        raise ProtocolError("Envelope must be a YAML mapping.")
    return _validate(raw, recipient, now or datetime.now(UTC))


def _validate(raw: Mapping[str, Any], recipient: str, now: datetime) -> HandoffEnvelope:
    if set(raw) != FIELDS:
        raise ProtocolError("Envelope fields are missing or unknown.")
    if raw["protocol_version"] != PROTOCOL_VERSION:
        raise ProtocolError("Unsupported protocol version.")
    for key in ("message_id", "correlation_id"):
        _uuid(raw[key], key)
    if raw["reply_to"] is not None: _uuid(raw["reply_to"], "reply_to")
    if raw["sender"] not in {"jarvis", "mitir"} or raw["recipient"] not in {"jarvis", "mitir"} or raw["sender"] == raw["recipient"]:
        raise ProtocolError("Sender and recipient must be different protocol participants.")
    if raw["recipient"] != recipient: raise ProtocolError("Envelope is addressed to another recipient.")
    if raw["type"] not in TYPES or raw["status"] not in STATES or raw["execution_level"] not in LEVELS:
        raise ProtocolError("Envelope type, state, or execution level is unsupported.")
    if (raw["type"] in REQUESTS) != (raw["reply_to"] is None):
        raise ProtocolError("Request/response reply_to is invalid.")
    created_at, expires_at = _timestamp(raw["created_at"], "created_at"), _timestamp(raw["expires_at"], "expires_at")
    if expires_at <= now.astimezone(UTC): raise ProtocolError("Envelope has expired.")
    if not isinstance(raw["requires_approval"], bool) or not isinstance(raw["max_hops"], int) or isinstance(raw["max_hops"], bool) or not 0 <= raw["max_hops"] <= 16:
        raise ProtocolError("Envelope approval or hop fields are invalid.")
    payload = _payload(raw["type"], raw["payload"])
    prohibited = _strings(raw["prohibited_actions"], "Prohibited actions")
    if len(set(prohibited)) != len(prohibited): raise ProtocolError("Prohibited actions must be unique.")
    return HandoffEnvelope(str(raw["message_id"]), str(raw["correlation_id"]), created_at, raw["sender"], raw["recipient"], raw["type"], raw["status"], raw["reply_to"], raw["execution_level"], raw["requires_approval"], expires_at, raw["max_hops"], payload, tuple(prohibited), _artifacts(raw["artifacts"]))


def _uuid(value: Any, name: str) -> None:
    try:
        if not isinstance(value, str): raise ValueError
        UUID(value)
    except ValueError as exc: raise ProtocolError(f"{name} must be a UUID.") from exc


def _timestamp(value: Any, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
    except ValueError: parsed = None
    if parsed is None or parsed.tzinfo is None: raise ProtocolError(f"{name} must be a timezone timestamp.")
    return parsed.astimezone(UTC)


def _payload(message_type: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, dict): raise ProtocolError("Payload must be a mapping.")
    required, optional = PAYLOAD_FIELDS[message_type]
    if not required <= set(value) or set(value) - required - optional: raise ProtocolError("Payload fields are not allowed for this message type.")
    strings = {
        "implementation_request": ("task_id", "title"), "documentation_request": ("task_id", "title"),
        "review_request": ("task_id", "subject"), "status_response": ("summary",),
        "result_response": ("summary", "test_summary"), "approval_request": ("subject", "reason"),
        "cancellation_request": ("reason",), "error_response": ("category", "summary"),
    }
    for key in strings.get(message_type, ()):
        _string(value[key], "Payload value")
    if message_type in {"implementation_request", "documentation_request"}:
        _strings(value["scope"], "Payload scope")
        for key in ("required_tests",):
            if key in value: _strings(value[key], "Payload tests")
        if "instructions" in value: _string(value["instructions"], "Payload instructions")
    if message_type == "review_request" and "files" in value: _strings(value["files"], "Payload files")
    if message_type == "approval_response":
        if value["decision"] not in {"approved", "rejected"}: raise ProtocolError("Approval decision is invalid.")
        if "approval_reference" in value: _string(value["approval_reference"], "Approval reference")
    if message_type == "error_response" and value["category"] not in {"protocol", "policy", "transport", "execution", "timeout", "recovery"}:
        raise ProtocolError("Error category is invalid.")
    canonical_payload_sha256(value)
    return value


def _strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value): raise ProtocolError(f"{name} must be non-empty strings.")
    return value


def _string(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ProtocolError(f"{name} must be a non-empty string.")


def _artifacts(value: Any) -> tuple[Mapping[str, str], ...]:
    if not isinstance(value, list): raise ProtocolError("Artifacts must be a list.")
    checked = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"uri", "sha256", "description"} or any(not isinstance(item[key], str) or not item[key] for key in item) or not re.fullmatch(r"[A-Fa-f0-9]{64}", item["sha256"]):
            raise ProtocolError("Artifact is invalid.")
        checked.append(item)
    return tuple(checked)
