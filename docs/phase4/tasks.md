# Phase 4 Tasks — Human-Approved Research Mutation

Status: **Ready for VS Code/Codex implementation — Gate A first; Gate B contract-dependent**

Primary SDD:

- `docs/phase4/spec.md`
- `docs/phase4/architecture.md`
- `docs/phase4/testing.md`
- `docs/api/jarvis-mitir-openapi.yaml`
- `docs/from-MiTiR.md`
- MiTiR `docs/from-Jarvis.md`

Phase 3 is complete. Do not regress the conversational read-only Daily/Research/Trading paths.

## P4-T0 — Read SDD and inspect current implementation

- [x] Read `AGENTS.md` and all Phase 4 SDD files.
- [x] Inspect the current Phase 3 conversational router/service/presenter code before changing architecture.
- [x] Inspect proposal/persistence/state abstractions already present in JARVIS, if any.
- [x] Inspect current MiTiR OpenAPI and confirm there is no supported Research mutation capability yet.
- [x] Confirm internal MiTiR `/api/research/action` is not a permitted JARVIS integration boundary.

Done when: Codex reports the smallest implementation plan for Gate A and identifies exact files to extend.

## P4-T1 — Distinguish Research read vs mutation intent

- [x] Extend routing to classify Research read and Research mutation separately.
- [x] Keep Daily/Trading read behavior unchanged.
- [x] Continue to block Trading mutation.
- [x] Add deterministic tests for mutation/read/ambiguous examples.
- [x] Never translate a mutation request into a read request while claiming it executed.

Done when: routing behavior is deterministic and safe without network or LLM.

## P4-T2 — Add Research Action Proposal model/service

- [x] Add the smallest JARVIS-owned proposal model required by the spec.
- [x] Generate unique non-secret proposal IDs.
- [x] Preserve bounded user intent/target/options only.
- [x] Start in `proposed` or repository-equivalent state.
- [x] Produce a human-readable proposal/effect summary.
- [x] Verify proposal creation makes zero remote mutation calls.

Done when: a mutation request can be converted into a reviewable proposal with no side effect.

## P4-T3 — Implement proposal lifecycle and storage

- [x] Reuse an existing local store/session abstraction if one exists.
- [x] Otherwise implement the smallest clearly documented proposal store consistent with the current CLI/session architecture.
- [x] Support lookup, pending state, rejection, expiry/replacement, and transition validation.
- [x] Prevent stale/unknown proposal approval.
- [x] Ensure invalid transitions fail safely.

Done when: proposal state transitions are explicit and fake-testable.

## P4-T4 — Add explicit approve/reject conversational path

- [x] Proposal creation and approval must occur in distinct operations/turns.
- [x] Add explicit approval by proposal ID and/or exactly-one-pending-proposal context.
- [x] Add explicit reject behavior.
- [x] Ambiguous `OK/yes` with zero or multiple proposals must not authorize mutation.
- [x] Duplicate approval must be idempotent.
- [x] Rejected proposal must never submit remotely.

Done when: user approval is explicit, auditable at application level, and cannot accidentally execute.

## P4-T5 — Enforce the external-contract gate

- [x] Detect that current MiTiR contract has no supported Research mutation capability.
- [x] On approval, transition to `approved_pending_remote_contract` or equivalent.
- [x] Present a truthful Secretary response explaining that approval is recorded but remote execution is not yet available through the supported external contract.
- [x] Add tests proving no internal `/api/research/action` or ad-hoc HTTP call is attempted.
- [x] Do not modify MiTiR source/config from JARVIS for convenience.

Done when: Gate A is fully functional and safe even before MiTiR contract extension.

## P4-T6 — Complete local Gate A verification

- [x] Run all new routing/proposal/approval tests.
- [x] Run full JARVIS regression suite.
- [x] Verify Phase 3 conversational reads remain correct.
- [x] Verify Trading mutation remains locally blocked.
- [x] Run secret/output scan and `git diff --check`.
- [x] Record redacted Gate A evidence in this task file.

Done when: Gate A is green and the only blocker is the formal MiTiR mutation contract.

Gate A evidence (local only, 2026-08-15):

- Proposal state before decision: `proposed`; approved state: `approved_pending_remote_contract`.
- Remote mutation submitted: no (proposal lifecycle has no transport/client dependency).
- Tests: `pytest -q` — 37 passed; `git diff --check` — passed.
- Blocker: MiTiR Integration API v0.1.0 has no accepted external Research mutation capability. P4-T7 onward remains blocked.

## P4-T7 — Coordinate MiTiR contract extension

- [x] Read the request recorded in MiTiR `docs/from-Jarvis.md`.
- [x] Wait for MiTiR to accept/reject/adjust it through its SDD/handoff process.
- [x] Do not invent the final capability name/schema in JARVIS code before MiTiR publishes it.
- [x] Once published, synchronize the new OpenAPI/contract into JARVIS.
- [x] Add/update consumer contract tests before implementing remote submission.

Done when: JARVIS has an accepted, versioned external Research mutation contract and green contract tests.

Evidence (2026-08-16): MiTiR Integration API v0.2.0 publishes only `research.select_candidates`; JARVIS typed models and OpenAPI synchronize its closed input and `waiting_for_approval` result. Fake consumer tests cover the capability without network or secret.

## P4-T8 — Implement supported remote Research submission

Prerequisite: P4-T7 complete.

- [x] Reuse the existing typed `MiTiRClient`/task lifecycle.
- [x] Map only an explicitly approved proposal to the exact published capability/schema.
- [x] Preserve fresh correlation ID and stable idempotency strategy tied to the approved proposal.
- [x] Prevent duplicate submission on repeated approval.
- [x] Poll boundedly.
- [x] Preserve `waiting_for_approval` as a real MiTiR state; do not auto-approve it.
- [x] Map success/failure into JARVIS-owned conversational results.

Done when: fake-driven tests prove one approved proposal produces at most one supported external task.

Evidence (2026-08-16): `ResearchSelectionService` submits only an `approved_pending_remote_contract` proposal through `MiTiRClient`, derives a stable proposal-bound idempotency key, records the MiTiR confirmation metadata, and stops at `waiting_for_approval`. It exposes cancellation only through the published task cancellation route; it has no confirm/resume operation. Fake tests: `13 passed`.

## P4-T9 — Full regression and secret review

- [x] Run the complete JARVIS suite.
- [ ] Verify all Phase 1–3 behaviors remain green.
- [ ] Search staged diff/output for token, Authorization, Bearer values, raw environment dumps, or accidental internal-endpoint coupling.
- [x] Run `git diff --check`.

Done when: implementation is reviewable and safe for live testing.

Evidence (2026-08-16): local fake/contract suite `pytest -q` passed `70 passed`; Phase 1 through Phase 4 tests remained green. `git diff --check` and the changed-file secret-format scan passed. No live request, confirmation/resume call, internal endpoint, RM-T10 action, or Trading mutation occurred.

Correction (2026-08-16): the P4-T9 checklist criteria are complete. After response-binding validation was added, `pytest -q` passed `72 passed`, affected consumer tests passed `15 passed`, and the same diff/secret checks remained clean. The unchecked checklist markers above are superseded by this evidence pending a documentation-only normalization.

## P4-T10 — Explicit Windows live Research mutation acceptance

Prerequisites:

- P4-T7/T8 complete;
- MiTiR supports the accepted external Research mutation capability;
- user explicitly approves the exact live proposal/test.

- [ ] Confirm `/health` and `/capabilities` from Windows.
- [ ] Create/show one bounded non-sensitive Research proposal without side effect.
- [ ] Obtain explicit human approval in a separate turn/action.
- [ ] Submit exactly one external MiTiR task.
- [ ] Verify no duplicate on repeated approval/retry.
- [ ] If MiTiR returns `waiting_for_approval`, stop and present that requirement without auto-approval.
- [ ] Otherwise verify terminal result and readable Secretary response.
- [ ] Record only redacted task/correlation/state evidence.

Done when: one bounded Research mutation has been verified end-to-end through the supported contract and both approval boundaries are preserved.

## P4-T11 — Documentation, handoff, and Git closure

- [ ] Update Phase 4 SDD if implementation revealed justified architecture/contract adjustments.
- [ ] Update this file with redacted test/live evidence.
- [ ] Prepare useful MiTiR handoff/result through `docs/from-Jarvis.md` only.
- [ ] Review changed/staged files and confirm no secret material.
- [ ] Ask the user before commit/push of implementation/evidence work.

Done when: Phase 4 is documented, tested, cross-project state is clear, and publication is explicitly approved.

## Codex execution rules

- Work `P4-T0` through `P4-T6` now.
- P4-T7 onward is blocked until MiTiR accepts/publishes the external mutation contract.
- Do not call internal MiTiR `/api/research/action` or any undocumented internal endpoint.
- Do not add Trading mutation/order code.
- Do not auto-approve any MiTiR-side approval state.
- Do not use an external LLM/network in ordinary tests.
- Prefer existing Phase 3 architecture and existing typed client over new frameworks/transports.
- After each meaningful increment, report changed files, tests, result, blocker/open issue, and next task.
- Stop before implementation/evidence commit/push and ask for explicit approval.
