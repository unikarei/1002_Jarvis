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

- [ ] Read `AGENTS.md` and every Phase 3 document above.
- [ ] Inspect the actual Phase 2 implementation, including `DailySummaryService`, its presenter/CLI, `MiTiRClient`, typed models/errors, and all tests.
- [ ] Inspect existing JARVIS conversation/LLM abstractions before adding any new router or responder.
- [ ] Identify the smallest extension that can support Daily, Research, and Trading read-only conversational requests.
- [ ] Confirm no MiTiR API/source change is required.

Done when: Codex reports a concise implementation plan naming the existing modules to extend, any new files it proposes, and the acceptance criteria covered. Do not code before this report.

## P3-T1 — Add typed conversational routing

- [ ] Introduce or extend a small typed routing decision: Daily / Research / Trading / Clarify / Unsupported.
- [ ] Ensure mutating requests are distinguishable from read/status requests.
- [ ] Make routing deterministic and fully testable without network or external LLM.
- [ ] If an LLM interpreter is used, place it behind an injectable interface and validate its output against the fixed routing enum.
- [ ] Never accept an LLM-generated arbitrary capability ID, URL, payload, or action.

Done when: one message produces one validated routing decision and unsafe/ambiguous messages cannot directly invoke MiTiR.

## P3-T2 — Add Research Summary application path

- [ ] Add the smallest JARVIS-owned Research Summary service/use case consistent with Phase 2 architecture.
- [ ] Reuse the existing typed `MiTiRClient`/gateway.
- [ ] Submit only `research.summary` with `{}`.
- [ ] Use fresh request/correlation identity and bounded polling.
- [ ] Map only fields actually returned by MiTiR into a typed JARVIS result.
- [ ] Preserve safe task/correlation references for diagnostics only.
- [ ] Map configuration/transport/readiness/auth/capability/timeout/task/contract failures safely.

Done when: product code can obtain a Research summary without knowing MiTiR task/HTTP details.

## P3-T3 — Add Trading Context application path

- [ ] Add the smallest JARVIS-owned Trading Context service/use case consistent with Phase 2 architecture.
- [ ] Reuse the existing typed `MiTiRClient`/gateway.
- [ ] Submit only `trading.context` with a contract-valid bounded `limit` (prefer default 5 unless current code/contract justifies another choice).
- [ ] Map only fields actually returned into a typed JARVIS result.
- [ ] Clearly preserve read-only/paper-mode/risk context when returned; do not infer execution.
- [ ] Do not add any order/approval/strategy-mutation call.
- [ ] Map failures safely.

Done when: product code can obtain bounded Trading Lab context and there is no mutation path in Phase 3.

## P3-T4 — Add Secretary conversation service and response composition

- [ ] Add or extend one JARVIS Secretary conversation service equivalent to `respond(message)`.
- [ ] Route Daily to the existing Phase 2 Daily path, not a duplicate implementation.
- [ ] Route Research and Trading to the new read-only services.
- [ ] Ask a concise clarification or return unsupported/read-only guidance when appropriate.
- [ ] Render readable Secretary responses rather than raw MiTiR/task JSON.
- [ ] Ground every factual statement in the structured specialist result.
- [ ] If LLM-based phrasing is used, keep it optional/injectable and forbid unsupported facts.

Done when: natural-language requests can use all three read-only MiTiR capabilities through one application boundary.

## P3-T5 — Add the smallest conversational user entry point

- [ ] Inspect existing commands/entry points first.
- [ ] Prefer extending current CLI/application composition rather than adding a UI framework.
- [ ] Add a narrow command such as `jarvis-chat "<message>"` only if no suitable entry point exists.
- [ ] Default output must be human-readable and secret-free.
- [ ] Keep safe diagnostic metadata behind an explicit option if useful.
- [ ] Ensure the boundary can later be reused by GUI/voice without moving business logic into the CLI.

Done when: from VS Code/PowerShell the user can make one natural-language request and receive one Secretary response.

## P3-T6 — Unit and regression tests

- [ ] Test Daily/Research/Trading routing with no network.
- [ ] Test ambiguity and unsupported behavior.
- [ ] Test mutating Research/Trading requests are blocked and make no specialist mutation call.
- [ ] Test one baseline request invokes at most one specialist service.
- [ ] Test Research/Trading mapping with missing optional fields and no fabrication.
- [ ] Test all major failure categories and safe presentation.
- [ ] Test optional LLM/router/composer via fakes only.
- [ ] Run the entire JARVIS test suite.
- [ ] Confirm Phase 1 verifier/contract and Phase 2 Daily behavior remain green.

Done when: ordinary tests require no live MiTiR, token, or external LLM and the full suite is green.

## P3-T7 — Secret/configuration review

- [ ] Continue using `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` as runtime configuration.
- [ ] Reuse existing LLM/provider configuration if an LLM is introduced; do not create duplicate secret-loading conventions.
- [ ] Confirm no secret files are staged/tracked.
- [ ] Run diff/source checks for accidental Bearer/token values.
- [ ] Confirm `.gitignore` still covers token/cache/`.codex` paths.

Done when: Phase 3 can run locally without adding any secret material to source control.

## P3-T8 — Explicit Windows live acceptance

Prerequisite: stop and obtain explicit user approval before real live requests if the user has not already approved that execution in the current implementation cycle.

- [ ] Confirm Tailscale peer and TCP 8080 reachability.
- [ ] Confirm MiTiR `/health` ready/API `0.1.0`.
- [ ] Run one conversational Daily request as a Phase 2 regression.
- [ ] Run one conversational Research status request and verify `research.summary` succeeds.
- [ ] Run one conversational Trading Lab status request and verify `trading.context` succeeds with bounded input.
- [ ] Verify all three outputs are readable, grounded, and not raw task JSON.
- [ ] Run a mutating Trading request and verify it is blocked locally/read-only with no mutation attempted.
- [ ] Record only redacted API/task/correlation/domain/timestamp evidence.

Done when: the actual Windows JARVIS conversational path safely consumes all three MiTiR read capabilities.

## P3-T9 — Documentation, handoff, and Git closure

- [ ] Update Phase 3 SDD/tasks with actual architecture choices and redacted evidence.
- [ ] Update SDD first if implementation reveals a justified requirement/architecture adjustment.
- [ ] Run `git diff --check` and full test suite.
- [ ] Review staged files and confirm no secret material.
- [ ] Prepare a concise MiTiR handoff only if useful acceptance evidence or a genuine contract issue should be recorded.
- [ ] Stop and ask the user before committing or pushing implementation/evidence changes.

Done when: Phase 3 is tested, documented, reviewable, and ready for explicit user-approved Git publication.

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
