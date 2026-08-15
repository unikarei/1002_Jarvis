# Prj.JARVIS Tasks

## Current milestone

Phase 2 — Operational Daily Summary via MiTiR

Status: **Ready for VS Code/Codex implementation**

Primary SDD:

- `docs/phase2/spec.md`
- `docs/phase2/architecture.md`
- `docs/phase2/testing.md`
- `docs/api/jarvis-mitir-openapi.yaml`
- `docs/from-MiTiR.md`

## Phase 1 closure

Phase 1 Windows-origin Tailscale integration is complete.

Verified on 2026-08-15:

- Windows `MyMousePC` reached MiTiR Secretary on the Mac mini through Tailscale;
- `/health` returned ready/API `0.1.0`;
- Bearer authentication succeeded;
- `daily.summary` completed successfully;
- exact idempotent replay returned the same task;
- changed same-key request returned HTTP 409 `idempotency_conflict`;
- terminal cancellation retained the successful result;
- redacted verification was handed to MiTiR `docs/from-Jarvis.md`;
- JARVIS Phase 1 implementation and SDD are committed on `main`.

Do not repeat Phase 1 work unless a regression is found.

## Phase 2 implementation tasks for VS Code/Codex

### P2-T0 — Read SDD and inspect current architecture

- [ ] Read `AGENTS.md` and every Phase 2 document listed above.
- [ ] Inspect the existing JARVIS source tree before proposing new folders/classes.
- [ ] Inspect the current `MiTiRClient`, models, errors, verification command, CLI/application entry points, and tests.
- [ ] Identify the smallest existing boundary suitable for a reusable daily-summary use case.
- [ ] Confirm the implementation does not require a MiTiR API change.

Done when: Codex reports a short implementation plan naming the existing modules it will extend and the acceptance criteria it will satisfy.

### P2-T1 — Add a JARVIS-owned Daily Summary use case

- [ ] Add or extend an application/service boundary equivalent to `get_daily_summary()`.
- [ ] Reuse the existing typed `MiTiRClient`; do not create another HTTP stack.
- [ ] Submit only `daily.summary` with empty input.
- [ ] Use a fresh correlation ID and idempotency key for each user request.
- [ ] Poll with a bounded policy and accept only terminal `succeeded` as success.
- [ ] Keep task/correlation references available as safe diagnostics.

Done when: product/application code can request a Daily Summary without knowing MiTiR HTTP endpoints or task lifecycle details.

### P2-T2 — Define stable JARVIS result and failure mapping

- [ ] Map the MiTiR domain-summary result into a JARVIS-owned result model.
- [ ] Preserve reporting date/time, headline/summary, important items, alerts/actions, and source references when present.
- [ ] Do not invent absent fields.
- [ ] Map configuration, unreachable, not-ready, unauthorized, capability-unavailable, timeout, task-failed, and contract errors into stable JARVIS categories.
- [ ] Ensure normal errors do not expose Authorization/token values or raw tracebacks.

Done when: callers consume a stable JARVIS contract rather than a raw MiTiR task record.

### P2-T3 — Add the smallest user-accessible entry point

- [ ] Inspect existing CLI/application entry points first.
- [ ] Extend an existing entry point if suitable; otherwise add one narrow command for Daily Summary.
- [ ] Default output must be human-readable, not raw task JSON.
- [ ] Preserve an explicit developer/diagnostic option only if it is small and justified.
- [ ] Keep the design callable by a future conversational JARVIS layer.

Done when: from Windows/VS Code, the user can execute one clear command/path and read the current Daily Intelligence summary.

### P2-T4 — Unit and regression tests

- [ ] Add fake-driven tests for successful mapping.
- [ ] Test missing optional fields without fabricated content.
- [ ] Test all major failure mappings defined in Phase 2 spec.
- [ ] Test user-facing presentation separately from transport/task mechanics where practical.
- [ ] Run the entire JARVIS test suite.
- [ ] Confirm Phase 1 verification/contract tests continue to pass.

Done when: ordinary tests require no MiTiR network or secret and the full suite is green.

### P2-T5 — Secret/configuration hygiene

- [ ] Continue to read `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` from runtime configuration.
- [ ] Do not add token values or secret-bearing `.env` files to Git.
- [ ] Confirm `.gitignore` still excludes `mitir-token.env`, local caches, and `.codex/`.
- [ ] Search staged diff/output for accidental `Authorization`, `Bearer`, or token leakage before commit.

Done when: Phase 2 can run locally without adding any secret material to source control.

### P2-T6 — Explicit Windows live acceptance

Prerequisite: user approval before the real request.

- [ ] Confirm MiTiR `/health` is ready from `MyMousePC`.
- [ ] Run the new user-facing Daily Summary path against the real MiTiR Secretary.
- [ ] Verify the result came from `daily.summary` and reached terminal success.
- [ ] Verify the displayed output is readable and not raw task JSON.
- [ ] Record API version, task ID, correlation ID, terminal state, timestamp, and destination without secrets.
- [ ] If a defect is found, fix it through SDD/code/tests and rerun the full suite.

Done when: the first actual JARVIS product feature consumes MiTiR successfully from Windows.

### P2-T7 — Documentation, review, and handoff

- [ ] Update this task file with redacted evidence.
- [ ] Update Phase 2 SDD if implementation revealed a justified architecture adjustment.
- [ ] Run `git diff --check` and the full test suite.
- [ ] Review staged files and confirm no secret material.
- [ ] Ask the user before commit/push.
- [ ] Send a MiTiR handoff only if a MiTiR-side contract issue/change is discovered or useful integration evidence should be recorded.

Done when: Phase 2 implementation is reviewable, tested, documented, and ready for user-approved Git backup.

## Codex execution rules for Phase 2

- Work through `P2-T0` → `P2-T7`; parallelize unit-test/result-model work where safe, but do not skip SDD inspection.
- Prefer extending current code over creating a second architecture.
- Do not modify MiTiR source/configuration for convenience.
- Do not expose MiTiR publicly.
- Do not execute Research or Trading features as part of Phase 2 acceptance.
- Do not add voice/UI frameworks in this phase.
- Do not silently fabricate fallback data when MiTiR is unavailable.
- Do not commit or push implementation changes until the user explicitly approves.
- After each meaningful implementation increment, report changed files, tests run, result, and the next task.
