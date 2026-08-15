# Phase 2 Specification — Operational Daily Summary via MiTiR

## 1. Status

- Phase: Phase 2 operational integration
- Specification status: Approved baseline for VS Code/Codex implementation
- Depends on: completed Phase 1 Windows-origin MiTiR verification
- MiTiR contract: Integration API v0.1.0
- Primary capability: `daily.summary`

## 2. Goal

Turn the verified JARVIS→MiTiR connection into the first useful JARVIS feature.

A user-facing JARVIS path shall obtain the current MiTiR Daily Intelligence summary and present it in a concise, readable form without exposing MiTiR transport details, task lifecycle mechanics, secrets, or raw internal payloads.

Phase 2 is successful when JARVIS can reliably answer the operational equivalent of “今日のMiTiRサマリーを見せて” using the real `daily.summary` capability from the Windows JARVIS runtime.

## 3. Product behavior

The feature shall:

1. call MiTiR through the existing typed `MiTiRClient`;
2. use `daily.summary` with empty input only;
3. generate a fresh correlation ID and idempotency key per user request;
4. poll with bounded attempts until terminal state;
5. return the successful result through a JARVIS-owned application/service boundary;
6. render a compact user-facing summary rather than dumping raw task JSON;
7. preserve source/reference fields returned by MiTiR when available;
8. distinguish unavailable, unauthorized, timeout, contract, and capability failures;
9. never silently fabricate a daily summary when MiTiR is unavailable.

## 4. Functional requirements

### FR-01 Runtime configuration

- Read `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` from runtime environment/configuration.
- Do not commit either secret-bearing runtime file or token value.
- Reuse the Phase 1 client configuration rather than adding another HTTP implementation.

### FR-02 Application boundary

Introduce or extend a JARVIS-owned application-layer service for the daily summary use case.

The service should expose a small operation equivalent to:

`get_daily_summary() -> DailySummaryResult`

The exact class/module name may follow the existing repository architecture discovered by Codex. Do not create a parallel framework when an existing application/service boundary already fits.

### FR-03 MiTiR execution

The service shall:

- perform readiness validation through `/health` when appropriate;
- optionally confirm `daily.summary` capability availability before execution, while avoiding unnecessary repeated discovery on every request if a small bounded cache is justified;
- submit `daily.summary` with `{}`;
- poll to a terminal result;
- treat only `succeeded` as a successful summary result;
- retain task/correlation references for diagnostics without exposing secrets.

### FR-04 User-facing presentation

The normal output shall be readable by a person and prioritize:

- reporting date/time when available;
- headline or overall status;
- key daily items;
- alerts or items requiring attention;
- source/artifact references when useful.

Raw MiTiR JSON may be available only through an explicit diagnostic/developer path; it is not the default product output.

### FR-05 Failure behavior

JARVIS must report a clear bounded failure rather than inventing data.

Minimum categories:

- configuration missing;
- MiTiR unreachable/not ready;
- unauthorized;
- capability unavailable;
- timeout;
- MiTiR task failed;
- contract/response validation error.

Messages shown to the user must not include Bearer tokens, Authorization headers, environment contents, or stack traces by default.

### FR-06 First user-accessible entry point

Provide the smallest maintainable user-accessible entry point supported by the current JARVIS architecture. Prefer extending an existing CLI/application interface if one exists. If none exists, add a narrow command dedicated to Phase 2 rather than inventing a large UI framework.

The acceptance path must be runnable from VS Code/PowerShell on `MyMousePC`.

### FR-07 Observability

For one request, record or return enough non-secret metadata to diagnose:

- destination identity/base URL without credentials;
- correlation ID;
- MiTiR task ID;
- terminal state;
- elapsed time or timestamps;
- categorized failure code when unsuccessful.

## 5. Non-functional requirements

- NFR-01: private Tailscale path remains the expected transport.
- NFR-02: Bearer token remains runtime-only and redacted.
- NFR-03: no unbounded polling or retries.
- NFR-04: reuse typed models/client introduced in Phase 1.
- NFR-05: ordinary unit tests must not require live MiTiR/network/secrets.
- NFR-06: live acceptance remains explicit/opt-in.
- NFR-07: Phase 1 verification command and contract tests must continue to pass.

## 6. Out of scope

- changes to MiTiR API or MiTiR source unless a genuine contract defect is discovered;
- `research.summary` as an end-user feature;
- `trading.context` as an end-user feature;
- trading actions;
- voice interaction;
- autonomous scheduling/notifications;
- public Internet exposure;
- a general plugin framework.

## 7. Acceptance criteria

Phase 2 is accepted when:

1. JARVIS has a clear application-layer daily-summary use case using the existing MiTiR client;
2. unit tests cover successful result transformation and major failure categories without network access;
3. existing Phase 1/contract tests still pass;
4. a user-accessible command/path returns a readable Daily Intelligence result instead of raw task JSON;
5. an explicit live run from Windows succeeds against the real MiTiR Secretary;
6. no secret is emitted or committed;
7. `tasks.md` contains redacted evidence and the implementation is ready for user-approved commit/push.
