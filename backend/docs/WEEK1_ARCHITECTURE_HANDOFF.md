# Week 1 Architecture Handoff (Kiruthika)

Maps Week 1 deliverables to code and docs. Share with Yehor, Tazwar, Sunny.

## Contract endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/contracts/export-lifecycle` | Status enums |
| `GET /api/v1/contracts/validation-template` | Compliance issue shape |
| `GET /api/v1/contracts/jurisdictions` | Jurisdiction catalog |
| `GET /api/v1/contracts/compliance-presets` | Preset catalog |
| `GET /api/v1/contracts/workflow-spec` | Pipeline stages + owners |
| `GET /api/v1/contracts/export-model` | Canonical ExportModel template |

## Schemas

- `backend/app/schemas/export_contracts.py` — lifecycle, validation, formats
- `backend/app/schemas/export_model.py` — geometry + metadata model

## Docs

- `backend/docs/API_CONTRACTS_SUMMARY.md`
- `backend/docs/MIGRATION_RUNBOOK_WEEK1.md`
- `docs/COMPLIANCE_DOMAIN.md`
- `docs/adr/001-dxf-ifc-first-export-strategy.md`
- `docs/adr/002-revit-bridge-phase2.md`
- `docs/adr/003-queue-persistence-split.md`
- `docs/WEEK1_SIGNOFF.md`

## DB migration

`backend/app/db/migrations/002_week1_architecture_foundations.sql` — apply via runbook (Kiruthika only).

## Team rules

- **Yehor:** persistence APIs; no custom status strings
- **Tazwar:** queue transitions + `dxf-files` upload handoff
- **Sunny:** UI binds to contract enums only
- **Kiruthika:** schema/contract changes require lead review
