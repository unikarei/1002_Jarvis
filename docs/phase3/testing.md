# Phase 3 Verification Plan — Conversational Specialist Reads

## 1. Purpose

Verify that the JARVIS Secretary can safely route natural-language requests to the three documented read-only MiTiR capabilities and return grounded, readable responses without exposing integration mechanics or secrets.

## 2. Test layers

### Layer A — local routing and presentation

No network, no token, no external LLM.

Cover at minimum:

- Daily request routes to Daily only;
- Research request routes to Research only;
- Trading-status request routes to Trading only;
- ambiguous request causes clarification/unsupported response and no MiTiR call;
- mutating research/trading request is blocked by the read-only boundary and no MiTiR call occurs;
- one user request triggers at most one specialist call in the baseline implementation;
- successful structured results render without raw task JSON;
- optional/missing result fields are not fabricated;
- diagnostic mode contains only safe metadata.

If an LLM-backed router/composer exists, test it through an injected fake or a deterministic adapter contract. Ordinary tests must never call the external model.

### Layer B — specialist use-case tests

Use fake MiTiR client/gateway responses.

Research:

- submit only `research.summary` with `{}`;
- bounded polling;
- only terminal `succeeded` is successful;
- map present fields and references only;
- map transport/auth/capability/timeout/task/contract failures safely.

Trading:

- submit only `trading.context` with a bounded integer `limit`;
- default limit should be explicit and contract-valid;
- map present paper-trading/status/risk/activity fields only;
- never place an order or call an undocumented capability;
- map failures safely.

Daily:

- retain Phase 2 behavior and tests unchanged unless a justified compatible refactor is required.

### Layer C — full regression

Run the full JARVIS test suite and verify:

- Phase 1 contract/live-verifier unit coverage remains green;
- Phase 2 Daily Summary tests remain green;
- package install/import and CLI entry points remain valid;
- no ordinary test requires runtime secrets or network.

## 3. Secret checks before live execution

Confirm without printing values:

- `MITIR_BASE_URL` is set;
- `MITIR_INTEGRATION_TOKEN` is set;
- no token file is staged/tracked;
- staged/source diff does not contain a Bearer value or token assignment;
- `.gitignore` still covers known local secret/cache paths.

Do not paste the token into Codex chat, source, Markdown, screenshots, logs, or Git.

## 4. Windows live acceptance

Live acceptance is explicit and opt-in. Use the existing private Tailscale route and MiTiR API v0.1.0.

Preflight:

1. `tailscale status` / peer online;
2. TCP 8080 reachable;
3. `GET /health` ready/API 0.1.0.

Then exercise the conversational product path, not raw curl for the capability itself.

Required live scenarios:

1. Daily regression: a natural Daily Intelligence request returns the current readable Daily result.
2. Research: a natural Research status request selects `research.summary`, succeeds, and returns readable grounded content.
3. Trading: a natural Trading Lab status request selects `trading.context`, succeeds with a bounded limit, and clearly presents context as read-only/paper-oriented according to returned data.
4. Read-only guard: a mutating trading request such as an order instruction is not executed; no mutating MiTiR operation is attempted.

## 5. Evidence format

Record redacted evidence containing only what is useful, for example:

```text
Test time: <ISO 8601>
JARVIS host: MyMousePC
Destination: <MagicDNS or private IP, no credentials>
API version: 0.1.0
Scenario: research
Selected domain/capability: research / research.summary
Task ID: <UUID if diagnostic evidence is needed>
Correlation ID: <non-secret ID if needed>
Final state: succeeded
Presentation: readable / no raw task JSON
Secret scan: clean
```

For the read-only guard, record that no specialist mutation call occurred. Do not include the original secret-bearing environment or Authorization header.

## 6. Stop conditions

Stop and report rather than improvising when:

- MiTiR API version/contract differs from the pinned current contract;
- authentication fails after secure configuration is confirmed;
- a conversational path attempts an undocumented capability;
- a mutating request reaches a mutation/execution path;
- Research or Trading output cannot be mapped without inventing fields;
- an external LLM is required for ordinary tests;
- a secret appears in output or diff;
- implementation would require changing MiTiR source/configuration merely for convenience.

## 7. Completion

Before Phase 3 is complete:

1. update Phase 3 SDD/tasks with actual implementation choices and redacted evidence;
2. run `git diff --check` and the full JARVIS suite;
3. review staged files and secret hygiene;
4. prepare a MiTiR handoff only if useful acceptance evidence or a genuine contract issue should be recorded;
5. stop and ask the user before commit/push.
