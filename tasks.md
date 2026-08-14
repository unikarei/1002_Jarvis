# Prj.JARVIS Tasks

## Current milestone

Phase 1 — Windows-origin Tailscale integration with MiTiR API v0.1.0

Status: **Ready for VS Code/Codex implementation**

## User actions before implementation/test

- [ ] On Windows `MyMousePC`, run `git status` and confirm whether local changes exist.
- [ ] Pull this SDD baseline with `git pull origin main` after the worktree is safe.
- [ ] Confirm Mac mini `ohidemac-mini` and MiTiR Secretary are running.
- [ ] Confirm Windows and Mac mini are connected to the same Tailscale network.
- [ ] Securely configure the existing `MITIR_INTEGRATION_TOKEN` for the JARVIS runtime; never paste it into chat or Git.
- [ ] Approve the non-destructive live test using `daily.summary` with empty input.

## Implementation tasks for VS Code/Codex

### T1 — Read SDD baseline

- [ ] Read all documents required by `AGENTS.md`.
- [ ] Inspect current Git status and existing client/tests.
- [ ] Confirm no requirement conflicts with OpenAPI v0.1.0.

Done when: implementation plan cites the relevant requirements and acceptance criteria.

### T2 — Repair packaging/test declarations

- [ ] Add pytest and PyYAML as test/development dependencies using the smallest maintainable project configuration.
- [ ] Configure Hatch wheel packaging for `src/jarvis`.
- [ ] Verify clean installation/import under Python 3.12.

Done when: a clean environment can install the project/test dependencies and import `jarvis`.

### T3 — Preserve existing consumer contract coverage

- [ ] Run all seven existing contract tests.
- [ ] Fix only configuration or genuine defects required by the approved specification.
- [ ] Confirm OpenAPI snapshot remains aligned with blob SHA `fbd3b806c7e386e48428df8e051f660d342f38aa`.

Done when: all existing contract tests pass without secrets or network dependency.

### T4 — Implement opt-in live verification

- [ ] Propose the smallest maintainable form: a dedicated integration test marker or a separate verification command.
- [ ] Require `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` at runtime.
- [ ] Skip/fail clearly when prerequisites are absent; never run automatically in ordinary unit tests.
- [ ] Implement bounded polling, retry, redaction, and evidence capture.
- [ ] Cover the workflow defined in `docs/testing.md`.

Done when: the live test is opt-in, safe, bounded, and produces redacted evidence.

### T5 — Run Windows-origin preflight

- [ ] Verify Tailscale status and MagicDNS ping.
- [ ] Verify TCP port 8080.
- [ ] Verify `/health` returns ready/API v0.1.0.
- [ ] Use IPv4 fallback only if MagicDNS fails, and record which route was used.

Done when: Windows `MyMousePC` reaches the actual MiTiR Secretary through Tailscale.

### T6 — Run live end-to-end test

- [ ] Discover capabilities.
- [ ] Run `daily.summary` with empty input.
- [ ] Verify correlation ID and terminal success.
- [ ] Verify exact idempotent replay.
- [ ] Verify changed replay conflict.
- [ ] Verify terminal cancellation semantics.

Done when: every acceptance criterion in `docs/spec.md` is satisfied or a precise blocker is recorded.

### T7 — Report and hand off

- [ ] Redact all evidence.
- [ ] Update this task list with result references.
- [ ] Prepare the result for MiTiR `docs/from-Jarvis.md`.
- [ ] Ask the user before commit/push.

Done when: MiTiR can review the result without any secret exposure.

## Prohibited in this milestone

- [ ] Do not modify MiTiR source or configuration.
- [ ] Do not expose MiTiR publicly.
- [ ] Do not test trading operations.
- [ ] Do not begin unrelated JARVIS feature development.
- [ ] Do not commit or push implementation work without explicit user approval.

