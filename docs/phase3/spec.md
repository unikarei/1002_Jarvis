# Phase 3 Specification — Conversational Specialist Read Integration

## 1. Status

- Phase: Phase 3 conversational integration
- Specification status: Approved baseline for VS Code/Codex implementation
- Depends on: completed Phase 2 operational Daily Summary
- MiTiR contract: Integration API v0.1.0
- Read-only capabilities in scope: `daily.summary`, `research.summary`, `trading.context`

## 2. Goal

Turn the Phase 2 command-oriented MiTiR use case into a Secretary-style conversational JARVIS experience.

The user should be able to ask ordinary questions such as:

- 「今日のAIニュースはどう？」
- 「今のResearchの状況を教えて」
- 「Trading Labの状況は？」

JARVIS shall interpret the request, select at most one appropriate read-only MiTiR capability for the first increment, obtain the result through the existing typed MiTiR integration, and return a readable Secretary response. The user must not need to know capability IDs, task IDs, HTTP endpoints, polling, or Bearer authentication.

Phase 3 is intentionally read-only. It must not approve, create, modify, execute, or cancel research/trading work on behalf of the user beyond the already-safe MiTiR task lifecycle used to obtain bounded read results.

## 3. Product behavior

The conversational flow shall:

1. accept a natural-language user message;
2. classify it into one of: Daily Intelligence, Research, Trading Context, or unsupported/clarification;
3. select the corresponding MiTiR read capability;
4. call the existing JARVIS application/integration boundary rather than raw HTTP;
5. wait with bounded polling/retry behavior;
6. map the result into a JARVIS-owned specialist result;
7. synthesize a concise Secretary response grounded only in returned data;
8. preserve safe diagnostic references outside the normal answer when explicitly requested;
9. never invent a MiTiR result if the service is unavailable or the intent is ambiguous.

## 4. Functional requirements

### FR-01 Conversational Secretary boundary

Add or extend a JARVIS-owned conversation/orchestration boundary equivalent to:

`respond(message: str) -> SecretaryResponse`

The exact implementation must follow the repository structure discovered by Codex. Do not introduce a second framework if an existing application/service boundary can be extended.

The boundary owns intent selection and user-facing response composition, not HTTP details.

### FR-02 Intent routing

For Phase 3, supported intents are:

- Daily Intelligence -> `daily.summary` with `{}`;
- Research status/summary -> `research.summary` with `{}`;
- Trading status/context -> `trading.context` with a bounded default `limit` chosen from the existing contract, preferably `5` unless repository behavior justifies another value.

Routing must be testable without a network or external LLM.

If an LLM is used for natural-language interpretation or response synthesis, it must sit behind a small injectable interface with a deterministic test double. The LLM may select among the documented read-only intents and may phrase returned facts, but it may not invent new MiTiR capabilities or bypass JARVIS/MiTiR safety boundaries.

### FR-03 Ambiguity and unsupported requests

JARVIS shall not guess when the request does not map reliably to one supported intent.

It should either:

- ask one concise clarification question; or
- return a clear unsupported/read-only-boundary response.

Mutating requests such as “trade this”, “approve this research”, “start a new job”, or equivalent must not be translated into read capabilities as if they were executed.

### FR-04 Reuse Phase 2 application behavior

Reuse the Phase 1 typed `MiTiRClient` and Phase 2 application/result mapping where practical.

Generalize only when there is real duplication. Do not replace the working `DailySummaryService` merely to make the architecture look uniform.

Research and Trading read use cases may follow the same pattern as Daily Summary, but each must expose a JARVIS-owned result model instead of leaking raw MiTiR task records.

### FR-05 Research presentation

For `research.summary`, preserve only fields actually returned by MiTiR. Prefer presenting, when available:

- current status/summary;
- active or recent research items;
- important findings or alerts;
- relevant artifact/source references.

Do not claim a paper, finding, recommendation, or completion state that is absent from MiTiR data.

### FR-06 Trading context presentation

For `trading.context`, present a bounded paper-trading context only. Prefer, when available:

- paper/live mode indication;
- current strategy/status;
- recent bounded activity;
- portfolio/P&L/risk context supplied by MiTiR;
- warnings or review-needed states.

Phase 3 must not place orders, approve strategies, change positions, or imply that a trade was executed.

### FR-07 Response grounding

Every successful Secretary response must be traceable to the selected MiTiR result.

The default user output should not show raw JSON, task lifecycle fields, stack traces, Authorization headers, tokens, or environment values.

When useful, a response may state the source domain (Daily/Research/Trading) and reporting timestamp. Safe task/correlation IDs remain diagnostic-only.

### FR-08 Failure behavior

Map failures into stable conversational outcomes, including at minimum:

- configuration missing;
- MiTiR unreachable/not ready;
- unauthorized;
- capability unavailable;
- timeout;
- task failed;
- contract/response validation error;
- ambiguous or unsupported intent.

A failure response must not fabricate substitute content.

### FR-09 First conversational entry point

Provide the smallest maintainable user-accessible conversational entry point supported by current JARVIS architecture.

A narrow CLI/repl-style command is acceptable for this phase if no UI exists. Prefer a shape such as:

`jarvis-chat "<message>"`

or an equivalent existing command. The implementation must remain reusable by a future GUI/voice layer.

## 5. Non-functional requirements

- NFR-01: Tailscale remains the expected private transport to MiTiR.
- NFR-02: `MITIR_INTEGRATION_TOKEN` remains runtime-only and never enters Git/output.
- NFR-03: all remote operations remain bounded and read-only at the capability level.
- NFR-04: ordinary tests require no MiTiR network, secret, or external LLM.
- NFR-05: Phase 1 and Phase 2 commands/tests must remain functional.
- NFR-06: prefer composition and small interfaces over a generalized agent/plugin framework.
- NFR-07: user-visible wording must distinguish data received from MiTiR from JARVIS inference or clarification.

## 6. Out of scope

- research job creation, selection, approval, deletion, or mutation;
- trading strategy approval or order execution;
- live brokerage operations;
- autonomous scheduling/notifications;
- email/calendar/PC-control actions;
- voice input/output;
- public Internet exposure;
- unrestricted tool calling;
- redesign of MiTiR internals or API without a proven contract defect.

## 7. Acceptance criteria

Phase 3 is accepted when:

1. one conversational JARVIS entry point can route natural-language requests to all three documented read-only MiTiR capabilities;
2. Daily behavior reuses the completed Phase 2 path rather than regressing it;
3. Research and Trading results are represented by JARVIS-owned models/presenters rather than raw task JSON;
4. ambiguous and mutating requests are safely rejected or clarified;
5. unit tests cover routing, result transformation, failure mapping, and no-fabrication behavior without network/LLM dependencies;
6. the full existing JARVIS suite remains green;
7. explicit Windows live acceptance successfully exercises `research.summary` and `trading.context` plus one Daily conversational regression through the real MiTiR Secretary;
8. user-facing output is readable and contains no secrets;
9. evidence is recorded in SDD and any useful MiTiR handoff is redacted and limited to the permitted handoff file;
10. commit/push occurs only after explicit user approval.
