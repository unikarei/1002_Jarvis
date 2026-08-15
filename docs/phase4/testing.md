# Phase 4 Testing Plan — Human-Approved Research Mutation

## 1. Purpose

Verify that JARVIS can safely propose, approve/reject, and eventually submit one bounded Research mutation without weakening Phase 3 read-only behavior or bypassing the MiTiR external contract.

## 2. Test layers

### Layer A — deterministic routing tests

Verify without network or LLM that messages classify correctly into:

- Research read;
- Research mutation;
- Daily read;
- Trading read;
- Trading mutation blocked;
- ambiguous/clarification.

Mutation examples must not accidentally route to a read capability and claim execution.

### Layer B — proposal construction

For Research mutation intent, verify:

- proposal is created with unique ID;
- action/effect summary is readable;
- target/topic/reference is preserved when present;
- only bounded approved fields are represented;
- state begins as `proposed` or repository-equivalent;
- proposal creation causes zero MiTiR mutation calls;
- no secrets/headers/internal endpoints appear.

### Layer C — approval/rejection lifecycle

Verify:

- approve is a distinct operation/turn;
- reject transitions proposal and guarantees no remote mutation call;
- expired/stale proposal cannot be approved;
- unknown proposal cannot be approved;
- ambiguous “yes/OK” with zero or multiple pending proposals does not authorize mutation;
- duplicate approval is idempotent and cannot duplicate a remote task;
- invalid state transitions fail safely.

### Layer D — contract gate

Before MiTiR publishes a mutation capability, verify:

- explicit approval results in `approved_pending_remote_contract` or equivalent;
- no call is made to `/api/research/action` or any internal endpoint;
- no ad-hoc HTTP transport is introduced;
- user receives a truthful message that approval is recorded but remote execution is not yet available through the external contract.

### Layer E — consumer contract extension

After MiTiR accepts/publishes the mutation contract:

1. synchronize the updated OpenAPI into JARVIS;
2. verify its Git blob/hash or otherwise exact contract version according to existing repository practice;
3. add consumer contract tests for the new capability/schema/state behavior;
4. verify auth, idempotency, correlation, and structured error mapping;
5. verify any `waiting_for_approval` response is preserved and not auto-approved.

Do not run Layer F until Layer E is green.

### Layer F — fake remote submission

Using a fake gateway/client, verify:

- approved proposal becomes one supported external task request;
- the final MiTiR capability ID and payload match the published contract exactly;
- proposal identity maps to a stable idempotency strategy;
- exact duplicate approval/submission does not create duplicate work;
- terminal `succeeded` maps to readable conversation;
- `waiting_for_approval` maps to a second human-action-required response;
- failed/timeout/unreachable/unauthorized/contract errors are safely categorized.

### Layer G — full regression

Run the complete JARVIS suite and confirm Phase 1–3 behavior remains green, especially:

- Phase 1 live verifier/contract tests;
- Phase 2 daily summary command;
- Phase 3 conversational Daily/Research/Trading reads;
- local blocking of Trading mutation.

## 3. Explicit Windows live acceptance

A real Research mutation test requires separate explicit user approval and a published MiTiR external mutation contract.

Preflight:

1. working tree is understood/safe;
2. MiTiR `/health` ready;
3. authenticated `/capabilities` includes the accepted Research mutation capability;
4. current OpenAPI/consumer tests match that capability;
5. one bounded, non-sensitive Research proposal is selected;
6. human explicitly approves that exact proposal;
7. test output is configured to omit tokens/Authorization.

Live acceptance should verify:

- proposal first shown without side effect;
- explicit approval recorded;
- one external MiTiR task submitted, no duplicate;
- correlation/task references retained;
- if MiTiR asks for approval, JARVIS stops and presents that requirement;
- otherwise terminal result is reported truthfully;
- no Trading mutation occurs.

## 4. Stop conditions

Stop and report rather than improvising when:

- MiTiR external mutation capability is not published;
- implementation would require an internal MiTiR endpoint;
- API/OpenAPI versions differ;
- user approval is ambiguous;
- multiple proposals make an approval ambiguous;
- MiTiR returns an undocumented state/schema;
- secret material appears in output;
- a Trading mutation path is reached;
- duplicate approval would create duplicate work.

## 5. Evidence format

Record only safe evidence, for example:

```text
Phase: 4
Proposal ID: <non-secret id>
Intent: research_mutation
Proposal state before approval: proposed
Human decision: approved | rejected
External mutation contract: unavailable | <capability/version>
Remote task submitted: yes/no
MiTiR task ID: <if any>
Correlation ID: <if any>
MiTiR state: <if any>
Final JARVIS state: <state>
Regression tests: <count/result>
Secret scan: passed
```

Never record the token, Authorization header, environment contents, or hidden reasoning.

## 6. Completion

Phase 4 completion requires both:

- Gate A local proposal/approval safety verified; and
- Gate B supported external Research mutation verified from Windows after MiTiR contract acceptance.

If Gate A completes before MiTiR contract acceptance, record Phase 4 as `blocked on external contract`, not as fully complete.
