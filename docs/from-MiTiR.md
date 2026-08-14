# From MiTiR to JARVIS

Status: Cross-project handoff channel

## 2026-08-14 — Initial integration baseline

MiTiR has added an SDD baseline for JARVIS integration.

Expected operations:
- `GET /health`
- `GET /capabilities`
- `POST /tasks`
- `GET /tasks/{id}`
- `POST /tasks/{id}/cancel`

Task execution is asynchronous. Task creation uses a stable idempotency identity so retries do not duplicate work.

Initial states:
- `accepted`
- `queued`
- `running`
- `waiting_for_approval`
- `succeeded`
- `failed`
- `cancel_requested`
- `cancelled`

MiTiR safety and confirmation boundaries remain authoritative. The intended connection is private networking plus application-level authentication.

Please align the JARVIS client and contract tests with MiTiR `docs/api/jarvis-mitir-openapi.yaml`. Proposed changes should be sent through MiTiR `docs/from-Jarvis.md`.

Open items: final authentication mechanism, first exposed capability IDs, large-result artifact retrieval, and the cross-project test environment.

## 2026-08-14 — Integration API v0.1.0 implemented

- Status: implemented; JARVIS verification requested
- Contract: MiTiR `docs/api/jarvis-mitir-openapi.yaml` version 0.1.0
- Authentication: Bearer token from `MITIR_INTEGRATION_TOKEN`
- Capabilities: `daily.summary`, `research.summary`, `trading.context`
- Retry: exact `Idempotency-Key` replay returns the original task; a changed request returns HTTP 409
- Cancellation: idempotent; terminal tasks retain their terminal state and result
- Safety: only bounded reads are exposed; MiTiR confirmation, Research and paper-Trading boundaries remain authoritative

MiTiR verified JARVIS commit `8367303`. All seven consumer contract tests passed in an isolated
audit environment, and the actual JARVIS `MiTiRClient` completed health, capability discovery and
task create/poll/cancel against the MiTiR API.

JARVIS maintenance note: `PyYAML` and pytest are not declared, and Hatch cannot infer `src/jarvis`
for editable installation. Add test dependencies and configure
`[tool.hatch.build.targets.wheel] packages = ["src/jarvis"]` in a JARVIS-owned change.

## 2026-08-14 — Tailscale endpoint ready for Windows-origin verification

- Status: ready
- `MITIR_BASE_URL`: `http://ohidemac-mini.taild8cb51.ts.net:8080`
- IPv4 fallback: `http://100.72.156.117:8080`
- Runtime state: MiTiR Secretary is healthy and bound only to `100.72.156.117:8080`
- Authentication: configure the same `MITIR_INTEGRATION_TOKEN` securely in the JARVIS runtime;
  never record its value in Git or test output
- First non-destructive task: `daily.summary` with empty `input`

Verified over MagicDNS/Tailscale from the MiTiR host:

- API v0.1.0 health returned ready;
- all three authenticated capabilities were advertised;
- `daily.summary` reached `succeeded` and preserved its correlation ID;
- exact idempotency replay returned the original task ID;
- a changed request with the same key returned HTTP 409 `idempotency_conflict`, non-retryable;
- terminal cancellation returned the existing `succeeded` task, as required by the contract.

Remaining action: run the same flow from the Windows `MyMousePC` JARVIS host and report destination,
API version, task/correlation references and outcomes without exposing the Bearer token.

## 2026-08-15 — Windows-origin live test approved and network preflight passed

MiTiR is ready for the first real JARVIS-originating non-destructive task verification.

Verified from the actual Windows `MyMousePC` peer:

- MyMousePC `100.121.233.72` and `ohidemac-mini` `100.72.156.117` are online in the same tailnet;
- Tailscale ping from Windows to the Mac succeeds;
- Tailscale access policy now permits MyMousePC -> ohidemac-mini on `tcp:8080` while preserving the existing Ollama `tcp:11434` grant;
- `Test-NetConnection 100.72.156.117 -Port 8080` reports `TcpTestSucceeded : True`;
- `curl.exe http://100.72.156.117:8080/health` returns `status: ok`, API v0.1.0 and `ready: true`;
- the shared `MITIR_INTEGRATION_TOKEN` is configured in the JARVIS Windows runtime and MiTiR runtime without committing or pasting the token value.

Human approval has been given to proceed with the non-destructive live test using:

- capability: `daily.summary`
- input: `{}`
- fresh idempotency key and correlation ID
- bounded retry/polling
- no Research mutation
- no Trading operation

Before this test, immutable Git backup branches were created:

- MiTiR: `backup/pre-jarvis-daily-summary-live-20260815`
- JARVIS: `backup/pre-mitir-daily-summary-live-20260815`

JARVIS/VS Code/Codex: please continue from the repository SDD. First perform authenticated
`GET /capabilities`, confirm `daily.summary`, then execute the approved task lifecycle test. Capture
only redacted evidence. Verify terminal success, exact idempotent replay, changed-input conflict and
terminal cancellation semantics. If the live contract fails, record the precise blocker before
requesting any MiTiR code/configuration change. Return the result through MiTiR `docs/from-Jarvis.md`.
