# AGENTS.md — Prj.JARVIS Development Rules

## Purpose

This repository implements Prj.JARVIS, the user-facing personal AI secretary and top-level orchestrator. MiTiR-Base is a separate specialist execution platform. Integrate through the versioned API contract; never import MiTiR implementation code directly.

## Mandatory SDD workflow

For every implementation task:

1. Read `docs/spec.md`, `docs/architecture.md`, `docs/testing.md`, `tasks.md`, `docs/from-MiTiR.md`, and `docs/api/jarvis-mitir-openapi.yaml`.
2. Confirm the relevant task is defined with acceptance criteria before editing code.
3. Update specification documents first if requirements change.
4. Implement only the smallest task marked ready in `tasks.md`.
5. Run the required unit, contract, and integration checks.
6. Record evidence without secrets.
7. Stop and ask the user before any action requiring credentials, installation, destructive changes, external writes, or expanded scope.

## Current authorized scope

The next phase is limited to:

- correcting JARVIS packaging/test dependency declarations;
- preparing a Windows-origin integration test runner or test procedure;
- verifying MiTiR API v0.1.0 through Tailscale;
- reporting verified results through the approved handoff channel.

Do not implement voice, calendar, email, PC automation, long-term memory, or new agent orchestration in this phase.

## Repository boundaries

- JARVIS repository: normal read/write development scope.
- MiTiR-BASE repository: read-only except `docs/from-Jarvis.md`.
- MiTiR responses are read from JARVIS `docs/from-MiTiR.md`.
- Any proposed MiTiR change must be requested through MiTiR `docs/from-Jarvis.md`; do not edit MiTiR source or configuration.

## Security requirements

- Never commit, print, log, or paste `MITIR_INTEGRATION_TOKEN`.
- Do not place the token in command history when a safer environment-file or interactive mechanism is available.
- Use Tailscale/private networking; do not expose MiTiR to the public internet.
- `/health` is unauthenticated; all other integration operations require Bearer authentication.
- Test only the non-destructive `daily.summary` capability with empty input unless the user explicitly approves another capability.
- Redact Authorization headers and secret values from all evidence.

## Completion rules

A task is complete only when:

- required tests were actually executed;
- results and failures are reported accurately;
- acceptance criteria in `docs/spec.md` are met;
- `tasks.md` is updated with evidence references;
- no secret is present in Git diff or test output;
- cross-project results are prepared for `docs/from-Jarvis.md`.

Do not commit or push implementation changes unless the user explicitly requests it. The present SDD documentation commit is the baseline from which VS Code/Codex should work.

