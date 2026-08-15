# Phase 3 Tasks — Conversational Specialist Read Integration

Status: **Ready for VS Code/Codex implementation**

Primary SDD:

- `docs/phase3/spec.md`
- `docs/phase3/architecture.md`
- `docs/phase3/testing.md`
- `docs/phase2/spec.md`
- `docs/phase2/architecture.md`
- `docs/api/jarvis-mitir-openapi.yaml`
- `docs/from-MiTiR.md`

Phase 1 and Phase 2 are complete. Do not repeat them except for regression verification.

## P3-T0 — Read SDD and inspect current implementation

- [x] Read `AGENTS.md` and every Phase 3 document above.
- [x] Inspect the actual Phase 2 implementation, including `DailySummaryService`, its presenter/CLI, `MiTiRClient`, typed models/errors, and all tests.
- [x] Inspect existing JARVIS conversation/LLM abstractions before adding any new router or responder.
- [x] Identify the smallest extension that can support Daily, Research, and Trading read-only conversational requests.
- [x] Confirm no MiTiR API/source change is required.

Done when: Codex reports a concise implementation plan naming the existing modules to extend, any new files it proposes, and the acceptance criteria covered. Do not code before this report.

Evidence (2026-08-15): Inspected Phase 2 `DailySummaryService`, its CLI/presenter, the typed `MiTiRClient`, models/errors, and the full existing test tree. No conversation or LLM abstraction exists. Phase 3 will reuse `DailySummaryService` unchanged, add narrow JARVIS-owned read-only Research/Trading use cases in `src/jarvis/integrations/mitir`, and add a deterministic router, Secretary service, and `jarvis-chat` entry point without an LLM or a second transport stack. No MiTiR API/source change is required.

## P3-T1 — Add typed conversational routing

- [x] Introduce or extend a small typed routing decision: Daily / Research / Trading / Clarify / Unsupported.
- [x] Ensure mutating requests are distinguishable from read/status requests.
- [x] Make routing deterministic and fully testable without network or external LLM.
- [x] If an LLM interpreter is used, place it behind an injectable interface and validate its output against the fixed routing enum.
- [x] Never accept an LLM-generated arbitrary capability ID, URL, payload, or action.

Done when: one message produces one validated routing decision and unsafe/ambiguous messages cannot directly invoke MiTiR.

Evidence (2026-08-15): Added deterministic `IntentRouter` and typed `ConversationIntent`/`RoutingDecision` in `src/jarvis/conversation.py`. Supported read intents are fixed; blank/ambiguous/unsupported messages do not select a capability, and mutating keywords receive `read_only_boundary` before any specialist invocation. No LLM interface is needed for this deterministic first increment. Full suite: `18 passed in 1.20s`.

## P3-T2 — Add Research Summary application path

- [x] Add the smallest JARVIS-owned Research Summary service/use case consistent with Phase 2 architecture.
- [x] Reuse the existing typed `MiTiRClient`/gateway.
- [x] Submit only `research.summary` with `{}`.
- [x] Use fresh request/correlation identity and bounded polling.
- [x] Map only fields actually returned by MiTiR into a typed JARVIS result.
- [x] Preserve safe task/correlation references for diagnostics only.
- [x] Map configuration/transport/readiness/auth/capability/timeout/task/contract failures safely.

Done when: product code can obtain a Research summary without knowing MiTiR task/HTTP details.

Evidence (2026-08-15): Added `ResearchSummaryService` and JARVIS-owned `ResearchSummaryResult`, composed with the existing typed client through the bounded `ReadOnlySpecialistRunner`. It fixes the capability to `research.summary` with `{}`, produces fresh IDs, maps only present status/reporting/headline/items/alerts/source fields, and keeps task/correlation references diagnostic-only. Runtime composition maps missing/invalid configuration safely. Fake-driven suite: `22 passed in 1.04s`.

## P3-T3 — Add Trading Context application path

- [x] Add the smallest JARVIS-owned Trading Context service/use case consistent with Phase 2 architecture.
- [x] Reuse the existing typed `MiTiRClient`/gateway.
- [x] Submit only `trading.context` with a contract-valid bounded `limit` (prefer default 5 unless current code/contract justifies another choice).
- [x] Map only fields actually returned into a typed JARVIS result.
- [x] Clearly preserve read-only/paper-mode/risk context when returned; do not infer execution.
- [x] Do not add any order/approval/strategy-mutation call.
- [x] Map failures safely.

Done when: product code can obtain bounded Trading Lab context and there is no mutation path in Phase 3.

Evidence (2026-08-15): Added `TradingContextService` and JARVIS-owned `TradingContextResult` using the same bounded typed-client runner as Research. The only submitted capability is `trading.context` with contract-valid default payload `{"limit": 5}` (locally bounded to 1..100). It maps only returned status/reporting/headline/mode/activity/alerts/source fields. No order, approval, strategy, or mutation path was added. Full suite: `24 passed in 0.98s`.

## P3-T4 — Add Secretary conversation service and response composition

- [x] Add or extend one JARVIS Secretary conversation service equivalent to `respond(message)`.
- [x] Route Daily to the existing Phase 2 Daily path, not a duplicate implementation.
- [x] Route Research and Trading to the new read-only services.
- [x] Ask a concise clarification or return unsupported/read-only guidance when appropriate.
- [x] Render readable Secretary responses rather than raw MiTiR/task JSON.
- [x] Ground every factual statement in the structured specialist result.
- [x] If LLM-based phrasing is used, keep it optional/injectable and forbid unsupported facts.

Done when: natural-language requests can use all three read-only MiTiR capabilities through one application boundary.

Evidence (2026-08-15): Added `SecretaryService.respond()` and `SecretaryResponse` to the JARVIS conversation boundary. It invokes exactly one injected specialist for a supported intent, delegates Daily to the existing Phase 2 service, and uses deterministic composition of only returned structured fields. Clarify/unsupported/read-only-boundary responses invoke no specialist. No LLM was added. Full suite: `27 passed in 0.78s`.

## P3-T5 — Add the smallest conversational user entry point

- [x] Inspect existing commands/entry points first.
- [x] Prefer extending current CLI/application composition rather than adding a UI framework.
- [x] Add a narrow command such as `jarvis-chat "<message>"` only if no suitable entry point exists.
- [x] Default output must be human-readable and secret-free.
- [x] Keep safe diagnostic metadata behind an explicit option if useful.
- [x] Ensure the boundary can later be reused by GUI/voice without moving business logic into the CLI.

Done when: from VS Code/PowerShell the user can make one natural-language request and receive one Secretary response.

Evidence (2026-08-15): Added `jarvis-chat` as the narrow Phase 3 CLI. It composes one existing typed MiTiR client with the existing Daily service and the new Research/Trading read services; no UI framework or new transport was introduced. Normal output is Secretary text only; `--diagnostic` adds safe metadata only. Configuration absence exits safely with code 2. Full suite: `27 passed in 0.82s`.

## P3-T6 — Unit and regression tests

- [x] Test Daily/Research/Trading routing with no network.
- [x] Test ambiguity and unsupported behavior.
- [x] Test mutating Research/Trading requests are blocked and make no specialist mutation call.
- [x] Test one baseline request invokes at most one specialist service.
- [x] Test Research/Trading mapping with missing optional fields and no fabrication.
- [x] Test all major failure categories and safe presentation.
- [x] Test optional LLM/router/composer via fakes only.
- [x] Run the entire JARVIS test suite.
- [x] Confirm Phase 1 verifier/contract and Phase 2 Daily behavior remain green.

Done when: ordinary tests require no live MiTiR, token, or external LLM and the full suite is green.

Evidence (2026-08-15): Added fake-only routing, Secretary composition, Research/Trading mapping, and shared read-runner tests. They cover one-specialist selection, ambiguity/unsupported behavior, local read-only mutation blocking, missing optional result fields, readable grounded responses, safe failure categories, and bounded timeout. No LLM is introduced. Full suite including Phase 1/2 regression coverage: `29 passed in 0.86s`.

## P3-T7 — Secret/configuration review

- [x] Continue using `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` as runtime configuration.
- [x] Reuse existing LLM/provider configuration if an LLM is introduced; do not create duplicate secret-loading conventions.
- [x] Confirm no secret files are staged/tracked.
- [x] Run diff/source checks for accidental Bearer/token values.
- [x] Confirm `.gitignore` still covers token/cache/`.codex` paths.

Done when: Phase 3 can run locally without adding any secret material to source control.

Evidence (2026-08-15): Phase 3 runtime composition reads only the existing `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` names. No LLM/provider was added. `git check-ignore` confirmed `mitir-token.env`, cache, and `.codex` exclusions; diff checks and a diff-only Bearer/token-assignment scan passed with no secret-bearing values.

## P3-T8 — Explicit Windows live acceptance

Prerequisite: stop and obtain explicit user approval before real live requests if the user has not already approved that execution in the current implementation cycle.

- [x] Confirm Tailscale peer and TCP 8080 reachability.
- [x] Confirm MiTiR `/health` ready/API `0.1.0`.
- [x] Run one conversational Daily request as a Phase 2 regression.
- [x] Run one conversational Research status request and verify `research.summary` succeeds.
- [x] Run one conversational Trading Lab status request and verify `trading.context` succeeds with bounded input.
- [x] Verify all three outputs are readable, grounded, and not raw task JSON.
- [x] Run a mutating Trading request and verify it is blocked locally/read-only with no mutation attempted.
- [x] Record only redacted API/task/correlation/domain/timestamp evidence.

Done when: the actual Windows JARVIS conversational path safely consumes all three MiTiR read capabilities.

Evidence (2026-08-15): Approved Windows live acceptance used MagicDNS destination `ohidemac-mini.taild8cb51.ts.net:8080`; TCP 8080 succeeded and `/health` returned ready/API `0.1.0`. Conversational `jarvis-chat` requests completed: Daily task `7d4dd609-3d2b-4f87-ad6f-e68f25ea7e47`, correlation `jarvis-daily-summary-c15bda6f-6f15-4e84-9a9d-7e3194a46795`; Research task `198ac94a-4d23-42c6-a0c6-5fd303c6461e`, correlation `jarvis-research-summary-ed3d8d71-3188-466e-afdb-eb5ede462316`; Trading task `dbd53974-c7b2-452b-a2e7-72b05c67ea4c`, correlation `jarvis-trading-context-6952a609-c7e5-4a83-805a-4257db4d49e1`. All reached `succeeded` and rendered readable grounded text without raw task JSON or secret data. A `Buy this stock` request was blocked locally as read-only; no MiTiR mutation was attempted. The Windows console Unicode display defect found during the first Research attempt was fixed and full local tests then passed.

## P3-T9 — Documentation, handoff, and Git closure

- [x] Update Phase 3 SDD/tasks with actual architecture choices and redacted evidence.
- [x] Update SDD first if implementation reveals a justified requirement/architecture adjustment.
- [x] Run `git diff --check` and full test suite.
- [x] Review staged files and confirm no secret material.
- [x] Prepare a concise MiTiR handoff only if useful acceptance evidence or a genuine contract issue should be recorded.
- [ ] Stop and ask the user before committing or pushing implementation/evidence changes.

Done when: Phase 3 is tested, documented, reviewable, and ready for explicit user-approved Git publication.

Evidence (2026-08-15): Recorded the actual deterministic router/Secretary/read-only service architecture and redacted live acceptance in this task file. No specification change was required; the Windows legacy-console Unicode rendering defect was an implementation fix, covered by a local test. Full suite: `30 passed in 0.86s`; JARVIS and prepared MiTiR handoff diffs passed `git diff --check`. Secret-bearing diff scan and ignored-path checks are clean. Prepared a concise verified Phase 3 entry in the permitted MiTiR `docs/from-Jarvis.md` local clone. Commit and push remain pending explicit user approval.

## Codex execution rules

- Work in order `P3-T0` → `P3-T9` unless safe test/model work can be parallelized after T0.
- After each meaningful increment, report: changed files, tests run/result, open issue, next task.
- Do not rewrite working Phase 1/2 components for aesthetics.
- Do not modify MiTiR source/configuration for convenience.
- Do not add mutating Research or Trading operations.
- Do not add a generalized plugin/tool framework unless a concrete Phase 3 requirement proves it necessary.
- Do not use an external LLM in ordinary automated tests.
- Do not fabricate fallback specialist content when MiTiR is unavailable.
- Do not commit or push implementation changes until the user explicitly approves.
