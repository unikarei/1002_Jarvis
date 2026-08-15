# Phase 2 Test Plan — Operational Daily Summary

## 1. Test objective

Verify that the first real JARVIS product flow can obtain and present MiTiR Daily Intelligence safely, readably, and repeatably.

## 2. Required layers

### Layer A — unit/application tests

Use fakes only; no network or secret required.

Cover at least:

- successful `daily.summary` result mapping;
- preservation of reporting time, headline, key items, alerts, and references when present;
- missing optional fields without invented data;
- configuration error mapping;
- transport/unreachable mapping;
- unauthorized mapping;
- timeout mapping;
- failed-task mapping;
- malformed/unexpected result mapping;
- no secret material in normal error strings.

### Layer B — regression/contract tests

Run the complete current JARVIS test suite and retain Phase 1 MiTiR contract coverage.

The Phase 1 verification command must remain available and its unit tests must continue to pass.

### Layer C — local user-entry test

Run the new user-accessible path against a fake/stubbed use case or fixture and verify that the default output is human-readable rather than raw task JSON.

### Layer D — explicit live acceptance

Only after user approval and runtime prerequisites are present:

1. confirm `MITIR_BASE_URL` and `MITIR_INTEGRATION_TOKEN` are set without displaying the token;
2. confirm `/health` ready/API v0.1.0;
3. run the new Phase 2 user-facing daily-summary command/path from Windows `MyMousePC`;
4. verify it obtains the real `daily.summary` result;
5. verify output is readable and contains no Authorization/token data;
6. record non-secret task/correlation references and timestamp;
7. run the full local test suite again if live-test fixes were required.

## 3. Stop conditions

Stop and report instead of improvising when:

- MiTiR API version changes;
- authentication fails after runtime configuration is confirmed;
- a required field violates the documented contract;
- implementation would require changing MiTiR for convenience rather than a proven defect;
- any secret appears in output/logs;
- polling exceeds its configured bound.

## 4. Evidence

Record in `tasks.md`:

- local test count/result;
- user-facing command/path tested;
- live destination identifier without credentials;
- API version;
- task ID and correlation ID;
- terminal outcome;
- confirmation that output was readable and secret-free;
- any defects found and their resolution.

Do not record the Bearer token, Authorization header, environment dump, or secret-bearing file content.
