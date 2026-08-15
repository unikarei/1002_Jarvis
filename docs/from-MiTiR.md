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

## 2026-08-15 — Research mutation Integration API v0.2.0 contract ready

- Status: MiTiR implementation and local/private verification complete; JARVIS client sync required
- Contract source: MiTiR `docs/api/jarvis-mitir-openapi.yaml`, API version `0.2.0`
- New capability: `research.select_candidates`
- Existing read capabilities and paths are unchanged
- Capability metadata: `approval_required: true`
- No generic command, arbitrary tool, internal endpoint, Research execution/deletion, or Trading
  mutation is exposed

JARVIS v0.1.0 uses strict literals for the API version and capability IDs. Update those client models
and contract tests to v0.2.0 before attempting submission. Capability discovery should contain
exactly the three existing reads plus `research.select_candidates`.

The request `input` is closed and must contain exactly:

```json
{
  "proposal_id": "<JARVIS proposal UUID>",
  "approval_reference": "<non-secret Gate A approval reference, 1..200 characters>",
  "candidate_ids": ["<current MiTiR Research candidate ID>"]
}
```

`candidate_ids` must contain 1..20 unique non-empty IDs, each at most 200 characters. Unknown fields,
arbitrary topics/prompts/actions, and unknown current candidate IDs are rejected. Do not put an
approval token, Bearer token, prompt body, or other secret in `approval_reference`.

A valid new submission follows `accepted -> queued -> running -> waiting_for_approval` and returns:

```json
{
  "status": "waiting_for_approval",
  "proposal_id": "<same proposal UUID>",
  "candidate_ids": ["<same bounded candidate IDs>"],
  "mitir_confirmation_id": "<MiTiR confirmation UUID>",
  "expires_at": "<RFC 3339 timestamp>",
  "next_action": "await_mitir_confirmation_contract"
}
```

This state is intentionally non-terminal. JARVIS Gate A approval is provenance only and never
confirms the MiTiR action. MiTiR v0.2.0 exposes no external confirmation/resume route, so JARVIS must
stop and display the pending MiTiR confirmation. It must not retry with a new key to bypass that
boundary. Cancelling the integration task cancels its linked pending MiTiR confirmation before the
task becomes `cancelled`; no Research selection is changed while blocked or after cancellation.

Exact `Idempotency-Key` replay with the same capability/input returns the original task and does not
create a second confirmation. Reusing the key with changed input returns non-retryable HTTP 409
`idempotency_conflict`. Input validation is returned before task acceptance; current-candidate
validation is persisted as safe `domain_validation_failed`; unexpected internals remain redacted.

Safe future live-test shape (token intentionally omitted):

```text
POST /tasks
Idempotency-Key: jarvis-research-select-<fresh-uuid>
capability_id: research.select_candidates
input: use one candidate ID obtained from the synchronized, human-reviewed proposal context
expected state: waiting_for_approval
```

Do not run that mutation test yet. JARVIS may move its proposal from
`approved_pending_remote_contract` to client/contract synchronization, but remote submission still
requires explicit human approval under RM-T10. After approval, verify the waiting state, exact replay,
cancellation, unchanged Research selection, and absence of Trading activity; return redacted evidence
through MiTiR `docs/from-Jarvis.md`.
