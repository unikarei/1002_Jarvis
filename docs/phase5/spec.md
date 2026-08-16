# Phase 5 Specification — Git Handoff Automation

## 1. Status and scope

- Status: SDD complete; implementation is pending explicit approval.
- Initial release supports L0–L2 only and does not authorize Phase 4, RM-T10, MiTiR live mutation, or Trading mutation.
- This phase is a local development-operation capability and is independent of the MiTiR API client.

## 2. Handoff Protocol v1.0.0

Each handoff is a Markdown section with exactly one closed, machine-readable YAML envelope. The required fields are `protocol_version`, `message_id`, `correlation_id`, `created_at`, `sender`, `recipient`, `type`, `status`, `reply_to`, `execution_level`, `requires_approval`, `expires_at`, `max_hops`, `payload`, `prohibited_actions`, and `artifacts`.

`handoff-protocol-v1.schema.json` is the machine-readable JARVIS-side source for envelope and per-type payload validation. Its canonical JSON SHA-256 is recorded beside it. The peer must explicitly agree to the same normalized schema before its value is accepted as cross-project compatible.

`message_id` is globally unique; all timestamps are ISO 8601/RFC 3339 with timezone. Sender and recipient are only `jarvis` or `mitir` and must differ. Unknown envelope fields are rejected unless a later negotiated protocol version introduces them. Payload is validated using an allowlisted schema for its type. Malformed, expired, misaddressed, schema-invalid, or secret-bearing messages never invoke an agent. Credentials, tokens, Authorization headers, private keys, recovery codes, and other secrets are prohibited in every message, artifact, log, and result.

Supported types: `implementation_request`, `documentation_request`, `review_request`, `status_response`, `result_response`, `approval_request`, `approval_response`, `cancellation_request`, and `error_response`.

States: `requested`, `accepted`, `in_progress`, `blocked`, `approval_required`, `completed`, `failed`, `cancelled`, and `rejected`. Valid execution transitions are `requested -> accepted|rejected|cancelled`, `accepted -> in_progress|blocked|approval_required|cancelled`, and `in_progress -> completed|failed|blocked|approval_required|cancelled`. Completed, failed, cancelled, and rejected are terminal. Acknowledgements, state updates, results, failures, and cancellations are new correlated messages; the original incoming entry is immutable.

JARVIS and MiTiR maintain semantically identical envelope/state definitions and a normalized shared schema SHA-256. A mismatch blocks execution. Protocol change requires an explicit correlated agreement, version increment, documented backward compatibility, and consumer-contract tests.

## 3. Direction, ownership, and levels

JARVIS receives from this repository's `docs/from-MiTiR.md` and sends only by appending to MiTiR's `docs/from-Jarvis.md`. Both sides may read the other repository but may write only their designated outbound handoff document. Development work occurs only in the receiving repository.

| Level | Scope | Initial release |
| --- | --- | --- |
| L0 | inspection/reporting | supported |
| L1 | SDD/documentation only | supported |
| L2 | source changes/tests; stop before commit | supported |
| L3 | commit/push isolated task branch; stop before merge | disabled pending separate approval/testing |
| L4 | merge, deployment, live API/Trading mutation, destructive/consequential action | not implemented; always explicit approval |

Policy must enforce levels, `prohibited_actions`, repository rules, and approval. RM-T10 and all live MiTiR mutation remain blocked until separately approved; Trading mutation is prohibited. Generated agents cannot create subagents or recursively run the handoff runner.

## 4. Safety, persistence, and agent boundary

Use a dedicated monitoring clone, `git fetch`, and a comparison of `origin/main` SHA before parsing; never repeatedly pull a dirty developer tree. Default polling is 60 seconds (configurable, never below 30). Fetch/push retries are bounded exponential backoff with jitter. Conflicts stop and report; no force-push or direct-main push is permitted. Create one worktree and task branch per accepted message and serialize jobs per machine without discarding unrelated changes.

A Git-ignored SQLite store records message/correlation IDs, source SHA, canonical payload SHA-256, state, attempts, worktree, branch, resulting commit, test summary, timestamps, and error category. Exact ID/payload replay never re-executes and safely republishes prior result when appropriate. Same ID/different payload is rejected. There is one active execution per ID; recovery is deterministic; cancellation is idempotent and never claims a completed task was undone.

Parse and validate untrusted Markdown before constructing a fixed prompt from allowlisted fields. The prompt requires AGENTS.md and relevant SDD review, enforces level/prohibitions, uses a wall-clock timeout, captures structured output, redacts secrets, and stops safely at approval boundaries. `max_hops` is validated/decremented, correlation exchanges are bounded, messages addressed elsewhere are ignored, and status/result entries never automatically create requests.

## 5. Operations and acceptance

JARVIS runs on Windows with Python 3.12, local non-interactive Codex CLI, Windows Task Scheduler, separate monitoring/worktree roots, and OS credential storage or process environment only. Provide structured redacted logs, health/status, dry-run, one-shot, daemon, clean shutdown, stale-lock/disk checks, retention cleanup, visible blocked/approval states, and a kill switch that disables agents but permits inspection.

Acceptance requires local-Git and fake-agent tests for all L0–L2 behavior, dry-run and L2 acceptance without commit/push/merge/deployment/live mutation/Trading/destructive action, and no MiTiR write except the designated outbound handoff document. L3 remains a separately approved future task.
