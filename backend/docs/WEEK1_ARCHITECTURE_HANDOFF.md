# Week 1 Architecture Handoff (Kiruthika)

This handoff captures the Week 1 architectural outputs required by the team plans and maps them to implementation artifacts.

## Delivered Week 1 Artifacts

## 1) Shared contracts (implemented)

- `GET /api/v1/contracts/export-lifecycle`
- `GET /api/v1/contracts/validation-template`
- `GET /api/v1/contracts/jurisdictions`
- `GET /api/v1/contracts/compliance-presets`
- `GET /api/v1/contracts/workflow-spec`

Purpose:
- Gives backend, queue, and frontend one source of truth for states, validation shape, jurisdiction presets, and pipeline stages.

## 2) Canonical enums and schemas (implemented)

In `backend/app/schemas/export_contracts.py`:
- Export lifecycle states
- Validation severity and categories
- Export format contract (`dxf`, `ifc`, `dwg`, `revit_package`)
- Approval/review states
- Jurisdiction and compliance preset summary schemas

## 3) Persistence-ready domain model (implemented as migration)

In `backend/app/db/migrations/002_week1_architecture_foundations.sql`:
- `jurisdictions`
- `compliance_presets`
- `compliance_rules`
- `project_compliance_records`
- `compliance_exceptions`
- `export_jobs`

Purpose:
- Enables Week 2+ work without schema ambiguity.
- Keeps existing `projects/jobs/files` intact while adding an export-job orchestration model.

## Team Integration Instructions (Week 1 -> Week 2)

## Yehor
- Use contract endpoints as source of truth for response shapes.
- Start wiring `export_jobs` persistence in API layer (Week 2 persistence scope).
- Keep existing `jobs` table behavior unchanged for backward compatibility.

## Tazwar
- Align queue lifecycle transitions to `/contracts/export-lifecycle`.
- Use `/contracts/workflow-spec` stages for orchestration flow.
- Emit status updates that match canonical lifecycle values only.

## Sunny
- Bind export status badges and progress UX to contract enum values.
- Use jurisdiction/preset endpoints for compliance filters and metadata displays.
- Avoid hardcoded status strings outside shared contract values.

## Kiruthika (lead sign-off checklist)

- [ ] Confirm all team members use the contract endpoints in integration branches.
- [ ] Confirm no custom lifecycle/status variants are introduced.
- [ ] Confirm validation payload mapping includes severity/category/review-state.
- [ ] Confirm migration review with Yehor before applying in shared environments.

## Known Constraints

- Unit tests require local dependency `google.generativeai` due global app imports in test bootstrap.
- Migration is committed but not auto-applied; apply through your normal DB migration flow.

