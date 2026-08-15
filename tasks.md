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

Evidence (2026-08-14): Added the opt-in `jarvis-mitir-verify` command. It accepts bounded polling options and requires both runtime environment variables before any request. The baseline uses only `daily.summary` with `{}`; its same-key conflict probe uses `research.summary` with `{}` and must be rejected before dispatch. The emitted JSON includes destination and task evidence but never token/header values. Isolated test run: `8 passed in 0.84s`; command help and missing-environment guard were also verified without a live request.

Evidence (2026-08-15): The first approved live run reached MiTiR, authenticated successfully, and passed through exact idempotent replay. It stopped only because the prior conflict probe changed `requester`, which MiTiR does not use for idempotency identity. The probe now changes the contract-relevant `capability_id` to `research.summary` with empty input; local regression test result after the correction: `8 passed in 1.18s`. A fresh live run is required to record final redacted evidence.

### T5 — Run Windows-origin preflight

- [x] Verify Tailscale status and MagicDNS ping.
- [x] Verify TCP port 8080.
- [x] Verify `/health` returns ready/API v0.1.0.
- [x] Use IPv4 fallback only if MagicDNS fails, and record which route was used.

Done when: Windows `MyMousePC` reaches the actual MiTiR Secretary through Tailscale.

Evidence (2026-08-14): MagicDNS resolved `ohidemac-mini.taild8cb51.ts.net` to the expected private address `100.72.156.117`, but `Test-NetConnection` from Windows reported TCP port 8080 unreachable. The prerequisite is therefore not complete. Per `docs/spec.md`, the IPv4 fallback was not attempted because MagicDNS resolution itself succeeded. No `/health` or authenticated requests were made after this failure.

Evidence (2026-08-15): MiTiR handoff confirms Windows `MyMousePC` and `ohidemac-mini` are online in the same tailnet; Tailscale ping succeeded; `Test-NetConnection 100.72.156.117 -Port 8080` succeeded; and `/health` returned `ok`, API `0.1.0`, ready `true`. MagicDNS remained available, so no IPv4 fallback was used.

### T6 — Run live end-to-end test

- [x] Discover capabilities.
- [x] Run `daily.summary` with empty input.
- [x] Verify correlation ID and terminal success.
- [x] Verify exact idempotent replay.
- [x] Verify changed replay conflict.
- [x] Verify terminal cancellation semantics.

Done when: every acceptance criterion in `docs/spec.md` is satisfied or a precise blocker is recorded.

Evidence (2026-08-15): Initial live execution reached MiTiR and authenticated successfully but stopped at the changed-idempotent-replay assertion. The cause was a JARVIS verifier defect: changing `requester` was not a contract-relevant request change. The verifier now uses the rejected `research.summary` empty-input probe under the same key; rerun is pending to capture task and correlation references without secrets.

Evidence (2026-08-15): Corrected live command completed over MagicDNS. API `0.1.0`; health ready; capabilities `daily.summary`, `research.summary`, `trading.context`; task `938c50ec-6985-48f2-9c37-d2d32046c258`; correlation `jarvis-phase1-1bdf5890-ee4f-406f-9881-6c6a4eee1dc8`; final state `succeeded`; exact replay returned the same task; changed replay returned HTTP 409 `idempotency_conflict`, `retryable=false`; terminal cancellation returned `succeeded` with result retained. Timestamp: `2026-08-15T00:08:40.725919+00:00`. No token or Authorization data was recorded.

### T7 — Report and hand off

- [x] Redact all evidence.
- [x] Update this task list with result references.
- [x] Prepare the result for MiTiR `docs/from-Jarvis.md`.
- [x] Ask the user before commit/push.

Done when: MiTiR can review the result without any secret exposure.

Evidence (2026-08-15): Prepared a `verified` entry in the permitted MiTiR handoff file `docs/from-Jarvis.md`, in a local temporary clone of `unikarei/MiTiR-BASE`. It records the redacted Windows-origin outcome, task/correlation references, replay/conflict/cancellation semantics, and `8 passed` local regression result. `git diff --check` passed. After explicit user approval, only that file was committed and pushed to MiTiR `main` as `f963962` (`docs: record JARVIS Phase 1 verification`).

## Prohibited in this milestone

- [ ] Do not modify MiTiR source or configuration.
- [ ] Do not expose MiTiR publicly.
- [ ] Do not test trading operations.
- [ ] Do not begin unrelated JARVIS feature development.
- [ ] Do not commit or push implementation work without explicit user approval.
