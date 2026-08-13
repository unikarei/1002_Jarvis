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