# Phase 5 Testing Plan — Git Handoff Automation

Automated tests use temporary local Git repositories, temporary SQLite, fake clocks, and fake executors. They must not use live GitHub, live Codex mutation, live MiTiR API mutation, credentials, merge, deployment, Trading, or destructive operations.

Required coverage includes valid/invalid envelopes; unknown fields; malformed Markdown/YAML; expiry; protocol mismatch; exact/conflicting replay; duplicate active processing; cancellation before/during/after terminal state; restart recovery; stale locks; fetch/push failure/backoff; dirty-tree protection; branch collision; timeout; secret redaction; prompt-injection-like payload; loop/max-hop limits; safe result presentation; direct-main prohibition; no live/Trading mutation; no MiTiR modification except outbound handoff; Windows restart; disk/cleanup; and full JARVIS regression.

Run unit tests for parser/schema/state/policy/redaction/prompt; consumer contract tests for shared normalized schema/hash and semantics; two-repository local-Git integration tests for L0/L1/L2 result publication/replay/cancellation/recovery; dry-run with agent disabled; and L2 fake-agent acceptance proving no commit, push, merge, API mutation, Trading mutation, or destructive action. Any secret leak, non-designated MiTiR write, protocol mismatch, or attempted L3/L4 action blocks release.
