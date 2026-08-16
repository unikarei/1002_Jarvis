# Handoff Protocol v1.0.0 canonicalization

Status: Proposed shared contract; JARVIS agreement pending

The normalized schema SHA-256 is calculated as follows:

1. Decode `handoff-protocol-v1.schema.json` as UTF-8 JSON and reject duplicate object keys.
2. Serialize the parsed JSON value as UTF-8 with Unicode preserved, object keys sorted by Unicode
   code-point order, separators `,` and `:` with no added whitespace, and no trailing newline.
3. Calculate SHA-256 over those serialized bytes and encode it as lowercase hexadecimal.

Python reference expression for contract tests:

```python
hashlib.sha256(
    json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()
```

This algorithm is named `canonical-json-v1` for Handoff Protocol v1.0.0. It is used for the shared
schema artifact and for validated message/payload identity. Implementations must reject non-finite
JSON numbers; protocol schemas currently avoid numeric values where cross-language numeric
normalization could be ambiguous.

The recorded MiTiR digest is stored in `handoff-protocol-v1.sha256`. JARVIS must independently
normalize its semantically identical artifact and record the same digest before either runner may
execute a message. A mismatch blocks execution.

The language-neutral consumer corpus is `handoff-protocol-v1.fixtures.json`. Consumers merge each
valid case's `type`, `status`, `execution_level`, `reply_to` and `payload` over `base_envelope`, then
validate the resulting envelope. Invalid cases apply their described mutation to the base
documentation-request fixture and must fail with the recorded stable category. Fixtures do not
override the schema; disagreement is resolved by the schema and a versioned protocol decision.
