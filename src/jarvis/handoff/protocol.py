"""Side-effect-free consumer validation for canonical Handoff Protocol v1.0.0."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json, re
from typing import Any, Mapping
from uuid import UUID
import yaml

PROTOCOL_VERSION = "1.0.0"
TYPES = frozenset({"implementation_request", "documentation_request", "review_request", "status_response", "result_response", "approval_request", "approval_response", "cancellation_request", "error_response"})
STATES = frozenset({"requested", "accepted", "in_progress", "blocked", "approval_required", "completed", "failed", "cancelled", "rejected"})
LEVELS = frozenset({"L0", "L1", "L2", "L3", "L4"})
REQUESTS = frozenset({"implementation_request", "documentation_request", "review_request"})
FIELDS = frozenset({"protocol_version", "message_id", "correlation_id", "created_at", "sender", "recipient", "type", "status", "reply_to", "execution_level", "requires_approval", "expires_at", "max_hops", "payload", "prohibited_actions", "artifacts"})
PROHIBITED = frozenset({"commit", "push", "direct_push_main", "force_push", "merge", "deployment", "live_api_mutation", "rm_t10", "trading_mutation", "destructive_action", "external_message", "other_repository_write", "generic_remote_command", "recursive_agent", "recursive_handoff_runner"})
ERRORS = frozenset({"invalid_message", "expired", "protocol_mismatch", "protocol_conflict", "policy_rejected", "approval_required", "cancelled", "transport", "timeout", "git_conflict", "agent_failed", "test_failed", "recovery_required", "internal"})
PATH = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\).+$")

class ProtocolError(ValueError): pass
@dataclass(frozen=True)
class HandoffEnvelope:
    message_id: str; correlation_id: str; created_at: datetime; sender: str; recipient: str; type: str; status: str; reply_to: str | None; execution_level: str; requires_approval: bool; expires_at: datetime; max_hops: int; payload: Mapping[str, Any]; prohibited_actions: tuple[str, ...]; artifacts: tuple[Mapping[str, Any], ...]

def canonical_payload_sha256(payload: Mapping[str, Any]) -> str:
    try: text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc: raise ProtocolError("Payload is not canonical JSON.") from exc
    return sha256(text.encode()).hexdigest()

def parse_markdown_entry(markdown: str, *, recipient: str, now: datetime | None = None) -> HandoffEnvelope:
    blocks = re.findall(r"```ya?ml\s*\n(.*?)```", markdown, re.DOTALL | re.IGNORECASE)
    if len(blocks) != 1: raise ProtocolError("A handoff entry must contain exactly one YAML envelope.")
    try: raw = yaml.safe_load(blocks[0])
    except yaml.YAMLError as exc: raise ProtocolError("Envelope YAML is malformed.") from exc
    if not isinstance(raw, dict): raise ProtocolError("Envelope must be a YAML mapping.")
    return _validate(raw, recipient, now or datetime.now(UTC))

def _validate(raw: Mapping[str, Any], recipient: str, now: datetime) -> HandoffEnvelope:
    if recipient not in {"jarvis", "mitir"} or set(raw) != FIELDS: raise ProtocolError("Envelope fields are missing or unknown.")
    if raw["protocol_version"] != PROTOCOL_VERSION: raise ProtocolError("Unsupported protocol version.")
    for key in ("message_id", "correlation_id"): _uuid(raw[key], key)
    if raw["reply_to"] is not None: _uuid(raw["reply_to"], "reply_to")
    if raw["sender"] not in {"jarvis", "mitir"} or raw["recipient"] not in {"jarvis", "mitir"} or raw["sender"] == raw["recipient"] or raw["recipient"] != recipient: raise ProtocolError("Envelope routing is invalid.")
    if raw["type"] not in TYPES or raw["status"] not in STATES or raw["execution_level"] not in LEVELS: raise ProtocolError("Envelope type, state, or execution level is unsupported.")
    created, expires = _time(raw["created_at"], "created_at"), _time(raw["expires_at"], "expires_at")
    if expires <= now.astimezone(UTC): raise ProtocolError("Envelope has expired.")
    if not isinstance(raw["requires_approval"], bool) or not isinstance(raw["max_hops"], int) or isinstance(raw["max_hops"], bool) or not 1 <= raw["max_hops"] <= 8: raise ProtocolError("Envelope approval or hop fields are invalid.")
    payload = _payload(raw["type"], raw["payload"]); prohibited = _enum_list(raw["prohibited_actions"], PROHIBITED, 32)
    return HandoffEnvelope(str(raw["message_id"]), str(raw["correlation_id"]), created, raw["sender"], raw["recipient"], raw["type"], raw["status"], raw["reply_to"], raw["execution_level"], raw["requires_approval"], expires, raw["max_hops"], payload, tuple(prohibited), _artifacts(raw["artifacts"]))

def _payload(kind: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, dict): raise ProtocolError("Payload must be a mapping.")
    if kind in REQUESTS: _closed(value, {"objective", "scope_paths", "sdd_references", "acceptance_criteria", "required_tests"}); _text(value["objective"]); _paths(value["scope_paths"], 1, 64); _paths(value["sdd_references"], 1, 64); _texts(value["acceptance_criteria"], 1, 64); _texts(value["required_tests"], 1, 64)
    elif kind == "status_response": _closed(value, {"summary", "processing_state", "attempt_count"}, {"blocker"}); _text(value["summary"]); _enum(value["processing_state"], {"accepted", "in_progress", "blocked", "approval_required"}); _integer(value["attempt_count"], 0, 20); _nullable_text(value.get("blocker"))
    elif kind == "result_response": _closed(value, {"summary", "changed_paths", "test_summary", "resulting_commit_sha"}); _text(value["summary"]); _paths(value["changed_paths"], 0, 128); _text(value["test_summary"]); _sha(value["resulting_commit_sha"], 40, 64)
    elif kind == "approval_request": _closed(value, {"action", "reason", "requested_execution_level"}); _text(value["action"]); _text(value["reason"]); _enum(value["requested_execution_level"], LEVELS)
    elif kind == "approval_response": _closed(value, {"decision", "approved_message_id", "constraints"}); _enum(value["decision"], {"approved", "rejected"}); _uuid(value["approved_message_id"], "approved_message_id"); _texts(value["constraints"], 0, 32)
    elif kind == "cancellation_request": _closed(value, {"target_message_id", "reason"}); _uuid(value["target_message_id"], "target_message_id"); _text(value["reason"])
    else: _closed(value, {"code", "message", "retryable"}); _enum(value["code"], ERRORS); _text(value["message"]); _bool(value["retryable"])
    canonical_payload_sha256(value); return value

def _closed(v: Mapping[str, Any], required: set[str], optional: set[str] = set()):
    if not required <= set(v) or set(v) - required - optional: raise ProtocolError("Payload fields are not allowed for this message type.")
def _uuid(v: Any, n: str):
    try:
        if not isinstance(v, str): raise ValueError
        UUID(v)
    except ValueError as exc: raise ProtocolError(f"{n} must be a UUID.") from exc
def _time(v: Any, n: str) -> datetime:
    try: parsed = datetime.fromisoformat(v.replace("Z", "+00:00")) if isinstance(v, str) else None
    except ValueError: parsed = None
    if parsed is None or parsed.tzinfo is None: raise ProtocolError(f"{n} must be a timezone timestamp.")
    return parsed.astimezone(UTC)
def _text(v: Any):
    if not isinstance(v, str) or not 1 <= len(v) <= 2000: raise ProtocolError("Text value is invalid.")
def _nullable_text(v: Any):
    if v is not None: _text(v)
def _bool(v: Any):
    if not isinstance(v, bool): raise ProtocolError("Boolean value is invalid.")
def _integer(v: Any, low: int, high: int):
    if not isinstance(v, int) or isinstance(v, bool) or not low <= v <= high: raise ProtocolError("Integer value is invalid.")
def _enum(v: Any, allowed):
    if v not in allowed: raise ProtocolError("Enumerated value is invalid.")
def _paths(v: Any, low: int, high: int):
    if not isinstance(v, list) or not low <= len(v) <= high or len(set(v)) != len(v) or any(not isinstance(x, str) or not 1 <= len(x) <= 500 or not PATH.fullmatch(x) for x in v): raise ProtocolError("Path list is invalid.")
def _texts(v: Any, low: int, high: int):
    if not isinstance(v, list) or not low <= len(v) <= high or len(set(v)) != len(v): raise ProtocolError("Text list is invalid.")
    for x in v: _text(x)
def _enum_list(v: Any, allowed, high: int):
    if not isinstance(v, list) or len(v) > high or len(set(v)) != len(v) or any(x not in allowed for x in v): raise ProtocolError("List value is invalid.")
    return v
def _sha(v: Any, low: int, high: int):
    if v is not None and (not isinstance(v, str) or not re.fullmatch(rf"[0-9a-f]{{{low},{high}}}", v)): raise ProtocolError("SHA value is invalid.")
def _artifacts(v: Any):
    if not isinstance(v, list) or len(v) > 32: raise ProtocolError("Artifacts are invalid.")
    for x in v:
        if not isinstance(x, dict) or set(x) != {"kind", "reference", "sha256"}: raise ProtocolError("Artifact is invalid.")
        _enum(x["kind"], {"document", "diff", "test_report", "commit", "log_summary"}); _paths([x["reference"]], 1, 1); _sha(x["sha256"], 64, 64)
    return tuple(v)
