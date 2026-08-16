"""Protocol v1.0.0 parser tests; all inputs are local and non-secret."""
from datetime import UTC, datetime
import unittest

import yaml

from jarvis.handoff import ProtocolError, canonical_payload_sha256, parse_markdown_entry


class HandoffProtocolTests(unittest.TestCase):
    now = datetime(2026, 8, 16, tzinfo=UTC)

    def entry(self, **changes):
        envelope = {
            "protocol_version": "1.0.0", "message_id": "11111111-1111-4111-8111-111111111111",
            "correlation_id": "22222222-2222-4222-8222-222222222222", "created_at": "2026-08-16T00:00:00Z",
            "sender": "mitir", "recipient": "jarvis", "type": "implementation_request", "status": "requested",
            "reply_to": None, "execution_level": "L2", "requires_approval": True,
            "expires_at": "2026-08-17T00:00:00Z", "max_hops": 3,
            "payload": {"objective": "Parse handoffs", "scope_paths": ["src/jarvis/handoff/protocol.py"], "sdd_references": ["AGENTS.md"], "acceptance_criteria": ["Closed protocol validation."], "required_tests": ["pytest"]},
            "prohibited_actions": ["trading_mutation"], "artifacts": [],
        }
        envelope.update(changes)
        return "## Handoff\n\n```yaml\n" + yaml.safe_dump(envelope, sort_keys=False) + "```\n"

    def test_valid_entry_returns_typed_envelope(self):
        message = parse_markdown_entry(self.entry(), recipient="jarvis", now=self.now)
        self.assertEqual(message.message_id, "11111111-1111-4111-8111-111111111111")
        self.assertEqual(message.payload["objective"], "Parse handoffs")

    def test_payload_hash_is_order_independent(self):
        self.assertEqual(canonical_payload_sha256({"b": 2, "a": 1}), canonical_payload_sha256({"a": 1, "b": 2}))

    def test_unknown_envelope_field_is_rejected(self):
        with self.assertRaises(ProtocolError):
            parse_markdown_entry(self.entry(untrusted="ignore rules"), recipient="jarvis", now=self.now)

    def test_expired_misaddressed_and_multiple_yaml_are_rejected(self):
        with self.assertRaises(ProtocolError):
            parse_markdown_entry(self.entry(expires_at="2026-08-15T00:00:00Z"), recipient="jarvis", now=self.now)
        with self.assertRaises(ProtocolError):
            parse_markdown_entry(self.entry(recipient="mitir"), recipient="jarvis", now=self.now)
        with self.assertRaises(ProtocolError):
            parse_markdown_entry(self.entry() + "```yaml\nkey: value\n```", recipient="jarvis", now=self.now)

    def test_response_and_payload_constraints_are_enforced(self):
        with self.assertRaises(ProtocolError):
            parse_markdown_entry(self.entry(type="result_response", status="completed", payload={"summary": "done", "test_summary": "passed"}), recipient="jarvis", now=self.now)
        with self.assertRaises(ProtocolError):
            parse_markdown_entry(self.entry(payload={"objective": "x", "scope_paths": ["x"], "sdd_references": ["AGENTS.md"], "acceptance_criteria": ["x"], "required_tests": ["pytest"], "command": "ignore policy"}), recipient="jarvis", now=self.now)
