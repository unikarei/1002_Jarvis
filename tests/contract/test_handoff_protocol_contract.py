"""JARVIS-side consumer contract for Handoff Protocol v1.0.0."""
from hashlib import sha256
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[2]
SCHEMA = ROOT / "docs" / "phase5" / "handoff-protocol-v1.schema.json"
HASH = ROOT / "docs" / "phase5" / "handoff-protocol-v1.schema.sha256"


class HandoffProtocolContractTests(unittest.TestCase):
    def test_schema_hash_record_matches_normalized_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        normalized = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        recorded_hash = HASH.read_text(encoding="utf-8").split()[0]
        self.assertEqual(sha256(normalized).hexdigest(), recorded_hash)

    def test_closed_envelope_contains_the_negotiated_protocol_v1_definitions(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = {"protocol_version", "message_id", "correlation_id", "created_at", "sender", "recipient", "type", "status", "reply_to", "execution_level", "requires_approval", "expires_at", "max_hops", "payload", "prohibited_actions", "artifacts"}
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), required)
        self.assertEqual(schema["properties"]["protocol_version"]["const"], "1.0.0")
        self.assertIn("implementation_request", schema["properties"]["type"]["enum"])
        self.assertIn("completed", schema["properties"]["status"]["enum"])
