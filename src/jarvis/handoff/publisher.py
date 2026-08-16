"""Outbound-only correlated handoff result formatting."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4
import yaml


class OutboundHandoffWriter(Protocol):
    def append(self, markdown: str) -> None: ...


class ResultPublisher:
    def __init__(self, writer: OutboundHandoffWriter, *, clock=lambda: datetime.now(UTC)) -> None:
        self._writer, self._clock = writer, clock
    def publish_result(self, *, correlation_id: str, reply_to: str, summary: str, test_summary: str) -> str:
        return self._publish("result_response", "completed", correlation_id, reply_to, {"summary": summary, "test_summary": test_summary})
    def publish_error(self, *, correlation_id: str, reply_to: str, category: str, summary: str) -> str:
        return self._publish("error_response", "failed", correlation_id, reply_to, {"category": category, "summary": summary})
    def _publish(self, type: str, status: str, correlation_id: str, reply_to: str, payload: dict[str, str]) -> str:
        now = self._clock()
        envelope = {"protocol_version": "1.0.0", "message_id": str(uuid4()), "correlation_id": correlation_id, "created_at": now.isoformat(), "sender": "jarvis", "recipient": "mitir", "type": type, "status": status, "reply_to": reply_to, "execution_level": "L2", "requires_approval": False, "expires_at": (now + timedelta(days=7)).isoformat(), "max_hops": 3, "payload": payload, "prohibited_actions": ["trading_mutation", "live_mitir_mutation"], "artifacts": []}
        markdown = "## Handoff result\n\n```yaml\n" + yaml.safe_dump(envelope, sort_keys=False) + "```\n"
        self._writer.append(markdown)
        return envelope["message_id"]
