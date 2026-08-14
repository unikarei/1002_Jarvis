# Prj.JARVIS Tasks

## Current milestone

Phase 1 — Windows-origin Tailscale integration with MiTiR API v0.1.0

Status: **Ready for VS Code/Codex implementation**

## User actions before implementation/test

- [x] On Windows `MyMousePC`, run `git status` and confirm whether local changes exist.
- [x] Pull this SDD baseline with `git pull origin main` after the worktree is safe.
- [x] Confirm Mac mini `ohidemac-mini` and MiTiR Secretary are running.
- [x] Confirm Windows and Mac mini are connected to the same Tailscale network.
- [x] Confirm Windows can reach `ohidemac-mini` over Tailscale.
- [x] Securely configure the existing `MITIR_INTEGRATION_TOKEN` for the JARVIS runtime; never paste it into chat or Git.
- [x] Approve the non-destructive live test using `daily.summary` with empty input.

Evidence (2026-08-14): On Windows `MyMousePC`, `tailscale status --json` reported BackendState `Running`, MagicDNS enabled for `taild8cb51.ts.net`, and the Mac mini peer `ohidemac-mini.taild8cb51.ts.net` / `100.72.156.117` online in the same tailnet. No credentials or personal identifiers were recorded.

## Implementation tasks for VS Code/Codex

### T1 — Read SDD baseline

- [x] Read all documents required by `AGENTS.md`.
- [x] Inspect current Git status and existing client/tests.
- [x] Confirm no requirement conflicts with OpenAPI v0.1.0.

Done when: implementation plan cites the relevant requirements and acceptance criteria.

Evidence (2026-08-14): Reviewed the mandatory SDD documents and OpenAPI v0.1.0. The client/models and seven consumer contract tests align with FR-01 through FR-07 and the specified OpenAPI SHA. Worktree contained only untracked `.codex/`, which is preserved and out of scope.

### T2 — Repair packaging/test declarations

- [x] Add pytest and PyYAML as test/development dependencies using the smallest maintainable project configuration.
- [x] Configure Hatch wheel packaging for `src/jarvis`.
- [x] Verify clean installation/import under Python 3.12.

Done when: a clean environment can install the project/test dependencies and import `jarvis`.

Evidence (2026-08-14): In an isolated Python 3.12.10 virtual environment, `pip install -e '.[test]'` completed and `import jarvis` succeeded. No secrets were supplied or emitted.

### T3 — Preserve existing consumer contract coverage

- [x] Run all seven existing contract tests.
- [x] Fix only configuration or genuine defects required by the approved specification.
- [x] Confirm OpenAPI snapshot remains aligned with blob SHA `fbd3b806c7e386e48428df8e051f660d342f38aa`.

Done when: all existing contract tests pass without secrets or network dependency.

Evidence (2026-08-14): Isolated environment command `python -m pytest -q` reported `7 passed in 1.05s`. `git hash-object docs/api/jarvis-mitir-openapi.yaml` returned `fbd3b806c7e386e48428df8e051f660d342f38aa`. The test run used only fake transport and no credentials or network access.

### T4 — Implement opt-in live verification

- [x] Propose the smallest maintainable form: a dedicated integration test marker or a separate verification command.
- [x] Require `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` at runtime.
- [x] Skip/fail clearly when prerequisites are absent; never run automatically in ordinary unit tests.
- [x] Implement bounded polling, retry, redaction, and evidence capture.
- [x] Cover the workflow defined in `docs/testing.md`.

Done when: the live test is opt-in, safe, bounded, and produces redacted evidence.

Evidence (2026-08-14): Added the opt-in `jarvis-mitir-verify` command. It accepts bounded polling options, requires both runtime environment variables before any request, and uses only `daily.summary` with `{}`. The emitted JSON includes destination and task evidence but never token/header values. Isolated test run: `8 passed in 0.84s`; command help and missing-environment guard were also verified without a live request.

### T5 — Run Windows-origin preflight

- [ ] Verify Tailscale status and MagicDNS ping.
- [ ] Verify TCP port 8080.
- [ ] Verify `/health` returns ready/API v0.1.0.
- [ ] Use IPv4 fallback only if MagicDNS fails, and record which route was used.

Done when: Windows `MyMousePC` reaches the actual MiTiR Secretary through Tailscale.

Evidence (2026-08-14): MagicDNS resolved `ohidemac-mini.taild8cb51.ts.net` to the expected private address `100.72.156.117`, but `Test-NetConnection` from Windows reported TCP port 8080 unreachable. The prerequisite is therefore not complete. Per `docs/spec.md`, the IPv4 fallback was not attempted because MagicDNS resolution itself succeeded. No `/health` or authenticated requests were made after this failure.

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
