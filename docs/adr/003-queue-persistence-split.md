# ADR 003: Queue vs Persistence Responsibility Split

**Status:** Accepted (Week 1)  
**Owner:** Kiruthika

## Context

Export lifecycle touches API persistence, async workers, and frontend status UX. Overlap causes duplicate state machines.

## Decision

| Layer | Owner | Responsibility |
|-------|--------|----------------|
| HTTP CRUD, `export_jobs` rows, `files` metadata | **Yehor** | Create at `queued`; link artifacts |
| Status transitions, retries, worker execution | **Tazwar** | Advance states; upload to `dxf-files` |
| Contracts, validation rules, compliance schema | **Kiruthika** | Enums, payloads, preflight/postflight |
| UI status/progress | **Sunny** | Bind to `ExportResponse` + contracts |

## Consequences

- Single lifecycle enum: `export_contracts.ExportStatus`.
- Tazwar must not invent status strings.
- Yehor must not embed queue logic in route handlers.
