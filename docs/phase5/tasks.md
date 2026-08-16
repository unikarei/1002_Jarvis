# Phase 5 Tasks — Git Handoff Automation

Status: **SDD complete; implementation pending explicit approval.** All implementation tasks below are pending. No task authorizes MiTiR/Trading mutation, commit, push, merge, deployment, or destructive action.

| ID | Purpose | Dependencies | Components/files | Acceptance criteria | Required tests | Level | Approval | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P5-T1 | Protocol/schema definitions | — | protocol/schema | closed v1.0.0 + shared hash | schema/contract | L1 | yes | complete |
| P5-T2 | Parser/canonical hashing | T1 | parser/validator | invalid input rejected | parser/replay | L2 | yes | complete |
| P5-T3 | SQLite state store | T1 | state store | atomic idempotency/recovery | state tests | L2 | yes | complete |
| P5-T4 | Policy/level enforcement | T1,T3 | policy | L0–L2 only; L3/L4 denied | policy tests | L2 | yes | complete |
| P5-T5 | Safe Git inspection | T2,T4 | transport/poller | pinned SHA/no dirty edits | local Git | L2 | yes | complete |
| P5-T6 | Worktree/branch management | T3,T5 | worktree manager | isolation/collision stop | worktree | L2 | yes | complete |
| P5-T7 | Fixed prompt generation | T2,T4 | prompt builder | allowlist/no recursion | injection | L2 | yes | complete |
| P5-T8 | Mock executor | T7 | executor interface | timeout/structured output | executor | L2 | yes | complete |
| P5-T9 | Codex adapter interface | T8 | adapter | disabled by default | adapter fake | L2 | yes | complete |
| P5-T10 | Result/error publication | T2–T5 | publisher | outbound-only correlated append | publisher | L2 | yes | complete |
| P5-T11 | Replay/conflict handling | T2,T3,T10 | state/publisher | no repeat/conflict reject | replay | L2 | yes | complete |
| P5-T12 | Cancellation semantics | T3,T4,T8,T10 | state/executor | idempotent terminal-safe | cancellation | L2 | yes | complete |
| P5-T13 | Timeout/recovery | T3,T8 | recovery | deterministic restart | recovery | L2 | yes | complete |
| P5-T14 | Loop prevention | T1,T4,T10 | policy/publisher | hop/exchange limits | loop | L2 | yes | complete |
| P5-T15 | Secret redaction | T2,T8,T10 | redactor | no sensitive persistence/output | redaction | L2 | yes | complete |
| P5-T16 | Task Scheduler integration | T5,T13 | CLI/service | safe Windows lifecycle | Windows fake | L1 | yes | complete |
| P5-T17 | Unit suite | T1–T16 | tests | component suite green | unit | L2 | yes | complete |
| P5-T18 | Consumer contract suite | T1,T17 | contract tests | semantic/hash parity | contract | L2 | yes | complete |
| P5-T19 | Cross-repo integration | T5–T18 | integration tests | local two-repo flow | integration | L2 | yes | pending |
| P5-T20 | Dry-run rollout | T19 | CLI/runbook | inspection only | dry-run | L0 | yes | pending |
| P5-T21 | L2 acceptance | T19,T20 | runtime | stops pre-commit | acceptance | L2 | yes | pending |
| P5-T22 | Operator runbook | T20,T21 | docs | recovery/kill switch | review | L1 | yes | pending |
| P5-T23 | Future gated L3 | T22 | policy/adapter | separately approved/tested | L3 gate | L3 | explicit separate approval | pending |

P5-T1 evidence (2026-08-16): JARVIS mirrors the mutually verified closed v1.0.0 schema at `docs/phase5/handoff-protocol-v1.schema.json`. Its independently normalized `canonical-json-v1` SHA-256 is `5fbb72a6cfb2c1164c3b7096da7cd80d067df5bce10e90d2e9b491ab66e3245f`, recorded in `handoff-protocol-v1.schema.sha256`. MiTiR read-only verification confirmed schema, digest, and fixture-corpus agreement; runners remain blocked pending the final acknowledgement.

P5-T2 evidence (2026-08-16): added side-effect-free Markdown/YAML parsing and closed envelope/per-type payload validation in `jarvis.handoff`. It rejects unknown fields, malformed/multiple YAML blocks, expiration, wrong recipients, invalid request/response correlation, and unallowlisted payload fields; payload hashing uses canonical JSON SHA-256. `pytest -q tests/test_handoff_protocol.py`: 5 passed; full suite: 46 passed.

P5-T3 evidence (2026-08-16): added the Git-ignored `StateStore` with the required execution metadata, atomic registration, exact-replay detection, conflicting-payload rejection, and explicit updates. State tests plus protocol tests: 7 passed; full suite: 48 passed. No database file is stored in Git.

P5-T4 evidence (2026-08-16): added deny-by-default execution policy. It permits only L0–L2 without a message-level prohibition or pending approval, preserves L0 inspection under the kill switch, and rejects L3/L4, Trading, RM-T10, and live MiTiR mutation. Handoff tests: 11 passed; full suite: 52 passed.

P5-T5 evidence (2026-08-16): added read-only `GitTransport` for a dedicated monitoring clone. It uses `git fetch --prune origin main`, compares the pinned `origin/main` SHA before reading, and reads only a repository-relative document with `git show <sha>:<path>`; it has no pull/push operation. Mocked transport tests: 14 passed; full suite: 55 passed.

P5-T6–P5-T10 evidence (2026-08-16): added isolated branch/worktree command construction from a pinned SHA, fixed prompt construction, mocked and non-interactive Codex executor interfaces, and an outbound-only result publisher behind an injected writer. Tests use fakes only; no Git, Codex, or MiTiR operation occurred. Full suite: 61 passed.

P5-T11–P5-T15 evidence (2026-08-16): completed exact replay/conflict behavior, idempotent terminal-safe cancellation, deterministic interrupted-job blocking, max-hop/request-only loop controls, and conservative secret redaction. Full suite: 64 passed.

P5-T16/P5-T17 evidence (2026-08-16): added a limited-account, on-logon Task Scheduler command builder without registering a task. Unit tests use no external process; full suite: 65 passed. Scheduler registration remains an explicit operator action. A draft operator runbook exists for P5-T22, which remains pending its dry-run and L2 acceptance dependencies.

P5-T18 evidence (2026-08-16): MiTiR published the language-neutral corpus in commit `9b08903`. JARVIS mirrors it at `docs/phase5/handoff-protocol-v1.fixtures.json`; the shared canonical schema digest is `5fbb72a6cfb2c1164c3b7096da7cd80d067df5bce10e90d2e9b491ab66e3245f`. The JARVIS consumer contract test executes all 9 valid and 7 invalid shared cases through `parse_markdown_entry`; schema/hash and fixture tests pass. Full JARVIS suite: 68 passed. The result is ready for MiTiR read-only verification through the designated handoff channel.

Implementation order is P5-T2 through P5-T22, with P5-T23 outside the initial release.
