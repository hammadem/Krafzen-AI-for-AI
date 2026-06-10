# Compliance Domain & Jurisdiction Versioning

**Owner:** Kiruthika (Week 1)

## Domain model

| Entity | Table | Purpose |
|--------|-------|---------|
| Jurisdiction | `jurisdictions` | Catalog (`US_IRC_BASELINE`, …) |
| Preset | `compliance_presets` | Rule bundle per jurisdiction |
| Rule metadata | `compliance_rules` | Code, category, severity (engine Week 3+) |
| Project snapshot | `project_compliance_records` | Validation JSON + approval state |
| Exception | `compliance_exceptions` | Manual override audit |

## Versioning strategy

- **`jurisdiction_id`** — stable key (e.g. `US_IRC_BASELINE`).
- **`schema_version`** — integer on jurisdiction row; bump when element refs change.
- **`rule_version`** — string on preset (e.g. `us_irc_baseline@1`); bump when rules change.
- Validation issues must carry `jurisdiction` + `rule_version` for UI grouping.

## Storage

- **Structured results:** Postgres JSONB in `project_compliance_records.validation_payload`.
- **CAD artifacts:** Supabase `dxf-files` (not compliance bucket).
- Optional PDF reports: `krafzen-files` (Week 3+).

## API contracts

- Presets/jurisdictions: `GET /api/v1/contracts/jurisdictions`, `/compliance-presets`
- Issue shape: `GET /api/v1/contracts/validation-template`
- Per-export validation: `GET /api/v1/exports/{id}/validation` (Week 2+)
