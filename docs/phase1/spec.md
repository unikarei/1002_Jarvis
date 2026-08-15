# Phase 1 Specification — Windows-to-MiTiR Tailscale Integration

## 1. Status

- Phase: Phase 1 integration verification
- Specification status: Ready for implementation
- Contract: MiTiR Integration API v0.1.0
- Contract file: `docs/api/jarvis-mitir-openapi.yaml`
- Contract blob SHA: `fbd3b806c7e386e48428df8e051f660d342f38aa`
- MiTiR handoff: `docs/from-MiTiR.md`

## 2. Goal

Prove that JARVIS running on the Windows `MyMousePC` host can securely call the actual MiTiR Secretary API on the Mac mini through Tailscale and that the real responses conform to OpenAPI v0.1.0.

## 3. Confirmed MiTiR endpoint

- Preferred `MITIR_BASE_URL`: `http://ohidemac-mini.taild8cb51.ts.net:8080`
- IPv4 fallback: `http://100.72.156.117:8080`
- MiTiR binding: `100.72.156.117:8080` only
- Authentication variable: `MITIR_INTEGRATION_TOKEN`
- First non-destructive capability: `daily.summary`
- First task input: `{}`

The fallback address may be used only when MagicDNS resolution fails. Neither endpoint may be replaced by a public URL in this phase.

## 4. Functional requirements

### FR-01 Packaging and test environment

The JARVIS project shall:

- declare the test dependencies required by the existing tests, including pytest and PyYAML;
- configure Hatch to package `src/jarvis` explicitly;
- provide a reproducible Windows setup and test command;
- preserve Python 3.12 compatibility.

### FR-02 Connectivity preflight

From Windows `MyMousePC`, the operator shall be able to:

- confirm Tailscale is connected;
- resolve or ping `ohidemac-mini` through Tailscale;
- confirm TCP port 8080 is reachable;
- call unauthenticated `GET /health`.

### FR-03 Authenticated capability discovery

Using a Bearer token sourced from `MITIR_INTEGRATION_TOKEN`, JARVIS shall call `GET /capabilities` and validate:

- API version is `0.1.0`;
- `daily.summary`, `research.summary`, and `trading.context` are returned;
- response parsing uses the existing typed models.

### FR-04 Task lifecycle

JARVIS shall create a `daily.summary` task with:

- empty `input`;
- a unique, non-secret correlation ID;
- requester identifying JARVIS without personal secrets;
- a stable test-specific `Idempotency-Key`.

JARVIS shall poll `GET /tasks/{id}` with bounded attempts until a terminal state is reached. The expected terminal state for the baseline test is `succeeded`.

### FR-05 Idempotency

JARVIS shall verify:

- exact replay with the same `Idempotency-Key` and payload returns the original task ID;
- a changed request using that key returns HTTP 409 `idempotency_conflict` with `retryable=false`.

The conflict test must remain non-destructive. To exercise a contract-relevant change without
executing another capability, it shall submit `research.summary` with empty input using the
baseline task's `Idempotency-Key`; the API must reject it with HTTP 409 before dispatch.

### FR-06 Cancellation semantics

After the baseline task reaches `succeeded`, JARVIS shall call `POST /tasks/{id}/cancel` and confirm that the terminal task remains `succeeded` with its result retained.

### FR-07 Evidence and handoff

The test report shall include:

- destination hostname or fallback IP used;
- API version;
- task ID;
- correlation ID;
- final state;
- idempotency replay result;
- conflict result;
- terminal cancellation result;
- timestamps and command/test version where available.

The report shall not include the token, Authorization header, or other secrets. The final cross-project report shall be sent only through MiTiR `docs/from-Jarvis.md`.

## 5. Non-functional requirements

- NFR-01: Network access remains private to Tailscale.
- NFR-02: The token is read from the environment and never stored in Git.
- NFR-03: Polling and retries are bounded; the test must not wait indefinitely.
- NFR-04: Transport, API, contract-validation, and test-assertion failures are distinguishable.
- NFR-05: Logs and evidence redact secrets by default.
- NFR-06: Existing seven consumer contract tests continue to pass.

## 6. Acceptance criteria

Phase 1 is accepted when all of the following are true:

- packaging/test installation succeeds on Windows Python 3.12;
- existing contract tests pass;
- Tailscale health and TCP preflight pass from `MyMousePC`;
- `/health` reports ready with API `0.1.0`;
- authenticated capabilities match the contract;
- `daily.summary` succeeds and preserves correlation ID;
- exact idempotent replay returns the original task;
- changed replay returns non-retryable HTTP 409;
- terminal cancellation retains the successful task;
- evidence contains no secrets;
- the outcome is ready to record in MiTiR `docs/from-Jarvis.md`.

## 7. Out of scope

- public internet exposure;
- changes to MiTiR implementation;
- voice/UI/calendar/email/PC-control features;
- trading actions or financial transactions;
- `research.summary` or `trading.context` execution;
- load, stress, failover, or performance testing;
- automatic rotation or distribution of secrets.

## 8. Open questions

- How will the user securely obtain the existing `MITIR_INTEGRATION_TOKEN` value on the Windows host without copying it into chat or Git?
- Should the completed integration test become an opt-in pytest marker or a separate PowerShell/Python verification command? VS Code/Codex should propose the smallest maintainable option before implementation.
