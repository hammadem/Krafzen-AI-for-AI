# Week 1 API Contracts Summary (OpenAPI-aligned)

**Owner:** Kiruthika · Base path `/api/v1`

## Architecture contracts (read-only)

| Method | Path | Response model |
|--------|------|----------------|
| GET | `/contracts/export-lifecycle` | `ExportLifecycleContract` |
| GET | `/contracts/validation-template` | `ExportValidationPayload` |
| GET | `/contracts/jurisdictions` | `JurisdictionContractsResponse` |
| GET | `/contracts/compliance-presets` | `CompliancePresetsResponse` |
| GET | `/contracts/workflow-spec` | JSON (stages, owners, formats) |
| GET | `/contracts/export-model` | `ExportModel` |

## Lifecycle states (frozen)

`queued` → `processing` → `validating` → `requires_review` | `completed` | `failed` | `cancelled`

## Export formats

`dxf` | `ifc` | `dwg` | `revit_package`

## Validation issue (nested in ExportValidationPayload)

```json
{
  "category": "geometry",
  "severity": "error",
  "code": "ROOM_AREA_MIN",
  "message": "Room area below minimum.",
  "element_ref": "room-1",
  "suggested_fix": "Increase room dimensions.",
  "jurisdiction": "US_IRC_BASELINE",
  "rule_version": "us_irc_baseline@1",
  "review_state": "pending_review"
}
```

## ExportModel (canonical internal JSON)

See `backend/app/schemas/export_model.py` and `GET /contracts/export-model`.

## Ownership (Week 2 persistence)

| Endpoint | Owner |
|----------|--------|
| `POST/GET /exports`, retry | Yehor |
| Job advance/retry | Tazwar |
| `/exports/{id}/validation` | Kiruthika |
| Dashboard activity/notifications | Tazwar |

## Storage naming (accepted Week 1)

- Generated CAD: `dxf-files/{user_id}/{project_id}/{filename}`
- User uploads: `krafzen-files/{user_id}/{project_id}/{file_id}.{ext}`

See `backend/docs/storage-architecture.md`.
