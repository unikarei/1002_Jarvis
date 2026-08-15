# Phase 4 Specification — Conversational Research Action with Human Approval

## 1. Status

- Phase: Phase 4 controlled mutation integration
- Specification status: Approved baseline for VS Code/Codex implementation
- Depends on: completed Phase 3 conversational read integration
- Current MiTiR external contract: Integration API v0.2.0, including bounded `research.select_candidates`
- Mutation domain in scope: Research only
- Trading mutation/order execution: explicitly out of scope

## 2. Goal

Extend the JARVIS Secretary experience from read-only specialist access to one safe, explicit, human-approved Research action workflow.

The target user experience is:

1. the user asks JARVIS to do Research work in natural language;
2. JARVIS interprets the request and creates a bounded Research Action Proposal;
3. JARVIS shows exactly what it proposes to do and asks the human to approve or reject;
4. no remote mutation occurs before explicit approval;
5. after approval, JARVIS may submit the action to MiTiR only through a formally supported external integration contract;
6. JARVIS reports the resulting MiTiR task/result conversationally with safe diagnostics.

Phase 4 must not bypass MiTiR's own confirmation/safety boundary. JARVIS approval is necessary but is not authority to disable any MiTiR-side approval or validation.

## 3. Critical contract gate

MiTiR Integration API v0.2.0 exposes the three read capabilities plus bounded `research.select_candidates`.

- `daily.summary`
- `research.summary`
- `trading.context`

JARVIS MUST NOT call MiTiR internal `/api/research/action` or any undocumented/internal endpoint directly. The only Research mutation capability is `research.select_candidates`; its external confirmation route is not published.

Phase 4 is split into two gates:

### Gate A — JARVIS-local proposal and approval

May be implemented immediately using only JARVIS code and tests. It includes intent recognition, proposal construction, user confirmation, reject/cancel behavior, durable-enough in-process/application state, and safe presentation.

### Gate B — MiTiR remote Research mutation

May be implemented and live-tested only after MiTiR accepts and publishes a versioned external capability/contract for the approved Research mutation workflow. Until then, approved proposals must stop in a stable `approved_pending_remote_contract` or equivalent state and must not invoke an internal MiTiR endpoint.

## 4. Product behavior

### FR-01 Research mutation intent

JARVIS shall distinguish Research mutation intent from Phase 3 read-only Research status intent.

Examples of mutation intent:

- 「この候補を詳しく調べて」
- 「このテーマでResearchを実行して」
- 「このResearch候補を採用して進めて」

Examples that remain read-only:

- 「Researchの状況を教えて」
- 「今の候補を見せて」

Ambiguous requests must be clarified rather than executed.

### FR-02 Research Action Proposal

JARVIS shall create a JARVIS-owned proposal model containing only fields required for a safe user decision. Prefer fields equivalent to:

- proposal ID;
- action type;
- concise title;
- user intent summary;
- target Research item/topic/reference when available;
- bounded parameters/options;
- expected effect;
- whether MiTiR additional approval may still be required;
- created timestamp;
- proposal state.

The proposal must not contain secrets, raw Authorization data, hidden reasoning, or undocumented MiTiR internals.

### FR-03 Explicit human approval

A Research mutation proposal must never be remotely executed in the same conversational turn that first proposes it.

The human must perform a distinct explicit approve/reject action referring to the current proposal. Natural confirmation language may be supported only when it unambiguously refers to exactly one pending proposal.

Examples of acceptable approval:

- 「それで進めて」 when exactly one proposal is pending and JARVIS clearly repeats the action being approved;
- an explicit `approve <proposal-id>` developer/CLI path;
- a future GUI approval button.

Silence, unrelated messages, read requests, or ambiguous acknowledgements are not approval.

### FR-04 Proposal lifecycle

At minimum support stable states equivalent to:

- `proposed`
- `approved`
- `rejected`
- `expired`
- `approved_pending_remote_contract`
- `submitted`
- `succeeded`
- `failed`
- `cancelled`

Exact names may follow repository conventions, but invalid transitions must be blocked and tested.

### FR-05 Reject/cancel behavior

Rejecting a proposal must guarantee that no MiTiR Research mutation is submitted from that proposal.

A proposal should expire or become invalid after a bounded time or after replacement by a materially different proposal, unless repository architecture already provides a safer lifecycle.

### FR-06 Remote contract boundary

When MiTiR publishes a supported Research mutation capability, JARVIS shall integrate it through the existing typed `MiTiRClient`/task lifecycle rather than a second HTTP stack.

The preferred external shape is a bounded capability-based task rather than direct internal endpoint access. The exact capability ID and input schema are owned by MiTiR and must be accepted into both projects' SDD/OpenAPI before JARVIS code depends on them.

### FR-07 Double safety boundary

JARVIS must preserve both layers:

1. JARVIS human approval before remote mutation submission;
2. MiTiR-owned validation/confirmation/safety after submission.

If MiTiR returns `waiting_for_approval` or equivalent, JARVIS must present that state honestly and must not auto-approve it unless a later SDD explicitly defines a second human confirmation path.

### FR-08 Conversational result

After a submitted Research action reaches a terminal or approval-required state, JARVIS shall return a readable Secretary response containing only facts from the proposal and MiTiR result, plus safe references when useful.

No raw task JSON, token, Authorization header, environment dump, stack trace, or hidden reasoning appears in normal output.

### FR-09 Failure behavior

Classify at least:

- ambiguous mutation intent;
- no pending proposal;
- stale/expired proposal;
- invalid transition;
- remote contract unavailable;
- configuration missing;
- MiTiR unreachable/not ready;
- unauthorized;
- remote capability unavailable;
- timeout;
- waiting for MiTiR approval;
- task failed;
- contract/response validation error.

Failures must not silently fall back to execution through internal APIs.

## 5. Non-functional requirements

- NFR-01: ordinary tests require no network, secret, or external LLM.
- NFR-02: proposal/approval routing is deterministic and fake-testable.
- NFR-03: `MITIR_INTEGRATION_TOKEN` remains runtime-only and redacted.
- NFR-04: Phase 1–3 commands/tests remain green.
- NFR-05: Phase 4 Research mutation remains bounded; no generic unrestricted tool executor is introduced.
- NFR-06: all remote retries/polling are bounded and idempotent according to the published MiTiR contract.
- NFR-07: a local approval record is not presented as proof that MiTiR executed anything.

## 6. Out of scope

- Trading strategy approval, order placement, position change, brokerage access, or autonomous trading;
- automatic Research execution without an explicit human approval turn;
- JARVIS direct calls to MiTiR internal `/api/*` action endpoints;
- bypassing MiTiR confirmation or Research safety logic;
- public Internet exposure;
- voice/UI framework expansion;
- scheduling/autonomous recurring mutation;
- email/calendar/PC-control actions;
- unrestricted agent/tool execution.

## 7. Acceptance criteria

Phase 4 is accepted when:

1. JARVIS conversation distinguishes Research read vs Research mutation intent;
2. mutation intent produces a JARVIS-owned, human-readable proposal without remote side effects;
3. explicit approve and reject paths are separate from proposal creation and invalid transitions are blocked;
4. reject guarantees no remote Research mutation submission;
5. before MiTiR contract extension, approve reaches a truthful pending-contract state and does not call internal MiTiR endpoints;
6. MiTiR contract-extension request is recorded through the official handoff channel;
7. after MiTiR publishes/accepts the mutation contract, JARVIS updates its synced OpenAPI/typed boundary before remote implementation;
8. a user-approved Windows live test exercises exactly one bounded Research mutation through the supported external contract, while preserving any MiTiR-side approval state;
9. full regression tests pass and no secret is emitted/committed;
10. implementation/evidence commit and push occur only after explicit user approval.
