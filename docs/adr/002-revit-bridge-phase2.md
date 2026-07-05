# ADR 002: Revit Bridge Deferred to Phase 2

**Status:** Accepted (Week 1)  
**Owner:** Kiruthika

## Context

Revit API (.NET) integration is a separate product surface from the FastAPI cloud MVP.

## Decision

- Week 1–6: **No native `.rvt` generation** in backend workers.
- `revit_package` format = JSON manifest + geometry refs (`GET /contracts/revit-compatibility-mapping`).
- Revit ribbon/add-in is a **separate repo/track** after cloud export E2E is stable.

## Consequences

- Yehor stores `revit_package` artifacts like other formats in `files` / `export_jobs`.
- Sunny shows Revit as “package download” until plugin ships.
