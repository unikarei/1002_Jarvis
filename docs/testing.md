# Phase 1 Verification Plan — Windows-Origin Tailscale Test

## 1. Purpose

This plan defines the evidence required to verify the real JARVIS-to-MiTiR path. It is an implementation target for VS Code/Codex, not a claim that the Windows-origin test has already run.

## 2. Preconditions requiring the user

The user must:

1. Work on Windows `MyMousePC`, where the JARVIS repository is checked out.
2. Confirm the Mac mini and MiTiR Secretary remain powered on and running.
3. Confirm both hosts are signed in to the same Tailscale network.
4. Make the existing `MITIR_INTEGRATION_TOKEN` available to the JARVIS process without entering it into chat, source code, Markdown, screenshots, or Git.
5. Approve execution of the non-destructive live integration test.

Do not create a new token merely for convenience unless the MiTiR owner intentionally rotates/configures it on both sides.

## 3. Pull and inspect

From the Windows JARVIS repository:

```powershell
git status
git pull origin main
```

If `git status` shows local uncommitted changes, stop before pulling and resolve them deliberately.

After pulling, VS Code/Codex must read:

- `AGENTS.md`
- `docs/spec.md`
- `docs/architecture.md`
- `docs/testing.md`
- `tasks.md`
- `docs/from-MiTiR.md`
- `docs/api/jarvis-mitir-openapi.yaml`

## 4. Environment values

Use the preferred URL first:

```powershell
$env:MITIR_BASE_URL = "http://ohidemac-mini.taild8cb51.ts.net:8080"
```

Set `MITIR_INTEGRATION_TOKEN` securely in the local process/environment. Do not paste its value into Codex chat or commit it. The IPv4 fallback is:

```text
http://100.72.156.117:8080
```

## 5. Preflight sequence

Run or automate these checks in order:

1. `tailscale status`
2. `tailscale ping ohidemac-mini`
3. `Test-NetConnection ohidemac-mini.taild8cb51.ts.net -Port 8080`
4. `GET /health`

Do not continue to authenticated task execution if the health response is not ready or not API v0.1.0.

## 6. Test layers

### Layer A — local static/contract verification

- install project/test dependencies reproducibly;
- verify package import/install behavior;
- run the existing consumer contract tests;
- confirm OpenAPI snapshot SHA/contents remain aligned.

### Layer B — live read-only verification

- call `/health` without Authorization;
- call `/capabilities` with Authorization;
- assert all three documented capabilities.

### Layer C — bounded task lifecycle

- create `daily.summary` with empty input;
- poll with a fixed interval and maximum duration;
- assert `succeeded` and matching correlation ID;
- repeat exact request/key and assert same task ID;
- change the request while retaining the key and assert HTTP 409/non-retryable;
- cancel the succeeded task and assert it remains succeeded.

## 7. Evidence format

Record a compact result such as:

```text
Test time: <ISO 8601>
JARVIS host: MyMousePC
Destination: <MagicDNS or fallback IP; no token>
API version: 0.1.0
Health: ready
Capabilities: daily.summary, research.summary, trading.context
Task ID: <UUID>
Correlation ID: <non-secret ID>
Final state: succeeded
Exact replay: same task ID
Changed replay: 409 idempotency_conflict, retryable=false
Terminal cancel: succeeded retained
Contract tests: <count/result>
```

Before saving or sharing, search output for `Authorization`, `Bearer`, and the token value. Do not retain output containing secrets.

## 8. Stop conditions

Stop and report without improvising when:

- the token is missing or rejected;
- Tailscale/TCP connectivity fails;
- the actual API version differs from `0.1.0`;
- an actual response violates OpenAPI;
- the task enters an unexpected state or exceeds the bound;
- any secret appears in output;
- implementing the test requires changing MiTiR source/configuration.

## 9. Completion and handoff

After successful verification:

1. update `tasks.md` with redacted evidence;
2. prepare a concise result entry for MiTiR `docs/from-Jarvis.md`;
3. ask the user before committing or pushing implementation/evidence changes;
4. do not modify any other MiTiR file.

