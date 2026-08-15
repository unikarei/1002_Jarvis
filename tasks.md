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

- [x] Read `AGENTS.md` and every Phase 2 document listed above.
- [x] Inspect the existing JARVIS source tree before proposing new folders/classes.
- [x] Inspect the current `MiTiRClient`, models, errors, verification command, CLI/application entry points, and tests.
- [x] Identify the smallest existing boundary suitable for a reusable daily-summary use case.
- [x] Confirm the implementation does not require a MiTiR API change.

Done when: Codex reports a short implementation plan naming the existing modules it will extend and the acceptance criteria it will satisfy.

Evidence (2026-08-15): Phase 2 SDD and current source/tests were reviewed. The existing `src/jarvis/integrations/mitir` package is the smallest suitable boundary: P2 will reuse `MiTiRClient`, `TaskRequest`, `TaskRecord`, typed models, and MiTiR exceptions. Planned JARVIS-owned additions are a small daily-summary use case/result mapper, a human-readable presenter, and one narrow CLI entry point; no MiTiR API or source change is required.

### P2-T1 — Add a JARVIS-owned Daily Summary use case

- [x] Add or extend an application/service boundary equivalent to `get_daily_summary()`.
- [x] Reuse the existing typed `MiTiRClient`; do not create another HTTP stack.
- [x] Submit only `daily.summary` with empty input.
- [x] Use a fresh correlation ID and idempotency key for each user request.
- [x] Poll with a bounded policy and accept only terminal `succeeded` as success.
- [x] Keep task/correlation references available as safe diagnostics.

Done when: product/application code can request a Daily Summary without knowing MiTiR HTTP endpoints or task lifecycle details.

Evidence (2026-08-15): Added `DailySummaryService.get_daily_summary()` in `src/jarvis/integrations/mitir/daily_summary.py`. It composes the existing typed `MiTiRClient` interface, sends only `daily.summary` with `{}`, creates fresh correlation/idempotency IDs, polls with a configurable bound, and returns task/correlation diagnostics only through the JARVIS result boundary. Fake-driven test suite: `13 passed in 0.95s`.

### P2-T2 — Define stable JARVIS result and failure mapping

- [x] Map the MiTiR domain-summary result into a JARVIS-owned result model.
- [x] Preserve reporting date/time, headline/summary, important items, alerts/actions, and source references when present.
- [x] Do not invent absent fields.
- [x] Map configuration, unreachable, not-ready, unauthorized, capability-unavailable, timeout, task-failed, and contract errors into stable JARVIS categories.
- [x] Ensure normal errors do not expose Authorization/token values or raw tracebacks.

Done when: callers consume a stable JARVIS contract rather than a raw MiTiR task record.

Evidence (2026-08-15): Added JARVIS-owned `DailySummaryResult`, `DailySummaryError`, and `DailySummaryFailureCategory`. The mapper preserves only present domain-summary fields (`reporting_at`, `headline`, important items, alerts, source artifacts) and uses empty/None values for absent optional fields. Runtime configuration, transport, readiness, authorization, capability, timeout, failed-task, and contract conditions map to stable safe categories. Fake-driven suite: `14 passed in 1.11s`.

### P2-T3 — Add the smallest user-accessible entry point

- [x] Inspect existing CLI/application entry points first.
- [x] Extend an existing entry point if suitable; otherwise add one narrow command for Daily Summary.
- [x] Default output must be human-readable, not raw task JSON.
- [x] Preserve an explicit developer/diagnostic option only if it is small and justified.
- [x] Keep the design callable by a future conversational JARVIS layer.

Done when: from Windows/VS Code, the user can execute one clear command/path and read the current Daily Intelligence summary.

Evidence (2026-08-15): Added the narrow `jarvis-daily-summary` project command and a module entry point. Default presentation renders reporting metadata, headline, important items, alerts, and sources only; it does not dump raw task JSON or diagnostic identifiers. The use case remains independently callable for a future conversational layer. User-entry/presentation and full test suite: `15 passed in 0.89s`; missing configuration exits with a safe one-line `configuration_error`.

### P2-T4 — Unit and regression tests

- [x] Add fake-driven tests for successful mapping.
- [x] Test missing optional fields without fabricated content.
- [x] Test all major failure mappings defined in Phase 2 spec.
- [x] Test user-facing presentation separately from transport/task mechanics where practical.
- [x] Run the entire JARVIS test suite.
- [x] Confirm Phase 1 verification/contract tests continue to pass.

Done when: ordinary tests require no MiTiR network or secret and the full suite is green.

Evidence (2026-08-15): Added fake-driven application/presentation tests covering successful mapping, absent optional fields, configuration, unreachable, not-ready, unauthorized, capability-unavailable, timeout, failed-task, and malformed-result categories. Full local JARVIS suite, including existing Phase 1 verification and contract coverage: `15 passed in 0.89s`, with no network or runtime secret required.

### P2-T5 — Secret/configuration hygiene

- [x] Continue to read `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` from runtime configuration.
- [x] Do not add token values or secret-bearing `.env` files to Git.
- [x] Confirm `.gitignore` still excludes `mitir-token.env`, local caches, and `.codex/`.
- [x] Search staged diff/output for accidental `Authorization`, `Bearer`, or token leakage before commit.

Done when: Phase 2 can run locally without adding any secret material to source control.

Evidence (2026-08-15): Runtime composition continues to read only `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN`; tests inject fakes and never require either value. `.gitignore` excludes `mitir-token.env`, Python caches, `.pytest_cache`, and `.codex`. `git check-ignore` confirmed those paths, `git diff --check` passed, and a diff-only sensitive-format scan found no secret-bearing assignment or Authorization value.

### P2-T6 — Explicit Windows live acceptance

Prerequisite: user approval before the real request.

- [x] Confirm MiTiR `/health` is ready from `MyMousePC`.
- [x] Run the new user-facing Daily Summary path against the real MiTiR Secretary.
- [x] Verify the result came from `daily.summary` and reached terminal success.
- [x] Verify the displayed output is readable and not raw task JSON.
- [x] Record API version, task ID, correlation ID, terminal state, timestamp, and destination without secrets.
- [x] If a defect is found, fix it through SDD/code/tests and rerun the full suite.

Done when: the first actual JARVIS product feature consumes MiTiR successfully from Windows.

Evidence (2026-08-15): Approved Windows live execution of `jarvis-daily-summary --diagnostic` completed through MagicDNS destination `ohidemac-mini.taild8cb51.ts.net:8080`. Typed `/health` validation confirmed API `0.1.0` and readiness. The `daily.summary` task `b812376e-3a18-42e1-963f-9129a7c1563f` with correlation `jarvis-daily-summary-e003b7fc-c6b9-42a6-9901-b422d00815de` reached terminal `succeeded` at `2026-08-15T01:37:17.733225+00:00`. Default content was readable (reporting time, status, headline, five important items, alert, and source); it was not raw task JSON and contained no secret material. MiTiR reported a stale-artifact alert as domain content; JARVIS displayed it without fabrication. No live defect required a code fix.

### P2-T7 — Documentation, review, and handoff

- [x] Update this task file with redacted evidence.
- [x] Update Phase 2 SDD if implementation revealed a justified architecture adjustment.
- [x] Run `git diff --check` and the full test suite.
- [x] Review staged files and confirm no secret material.
- [ ] Ask the user before commit/push.
- [x] Send a MiTiR handoff only if a MiTiR-side contract issue/change is discovered or useful integration evidence should be recorded.

Done when: Phase 2 implementation is reviewable, tested, documented, and ready for user-approved Git backup.

Evidence (2026-08-15): Updated `docs/phase2/architecture.md` to document the deliberately narrow non-secret diagnostic option. Full JARVIS suite: `15 passed in 0.70s`; `git diff --check` and staged-diff check passed. Review covered tracked modifications plus the three new JARVIS source/test files; no token file is tracked, and `.gitignore` excludes token, cache, and `.codex` paths. Prepared a redacted Phase 2 verified-result entry in the permitted MiTiR `docs/from-Jarvis.md` local handoff clone. Commit and push remain pending explicit user approval.

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
