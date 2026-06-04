# Export API Documentation

_Last updated: June 4, 2026_

## Overview

The Export API allows users to create and track export requests for their projects.
Exports go through a defined lifecycle managed by the backend (creation), worker (processing), and are read by frontend.

---

## Export Lifecycle

```
queued
  └── processing
        └── validating
              ├── completed         export ready
              ├── failed            something went wrong
              ├── requires_review   needs manual review
              └── cancelled         export was cancelled
```

- **queued** — export created, waiting to be picked up by worker
- **processing** — Tazwar's worker is generating the file
- **validating** — file generated, running validation checks
- **completed** — export ready, file available for download
- **failed** — something went wrong, see `error_message`
- **requires_review** — needs manual review before completing
- **cancelled** — export was cancelled

---

## Endpoints

### Create Export

POST /api/v1/exports
**Request body:**

```json
{
  "project_id": "uuid",
  "format": "dxf | ifc | dwg | revit_package",
  "idempotency_key": "unique-string-required",
  "source_job_id": "uuid (optional)",
  "metadata": {}
}
```

**Response:** `ExportResponse` (status 201)

---

### Get Export

GET /api/v1/exports/{export_id}

**Response:** `ExportResponse`

---

### List Exports for Project

GET /api/v1/exports/project/{project_id}

**Response:** `ExportResponse[]` ordered by `created_at` desc

---

### Update Export Status

PATCH /api/v1/exports/{export_id}/status
**Request body:**

```json
{
  "status": "processing",
  "progress_percent": 50,
  "file_path": "path/to/file",
  "bucket": "krafzen-files",
  "error_message": null,
  "errors": null,
  "artifact_file_id": "uuid",
  "compliance_record_id": "uuid",
  "metadata": {
    "stage": "export_generation",
    "preset_id": "uuid",
    "artifact_urls": []
  },
  "retry_count": 0
}
```

**Response:** `ExportResponse`

---

## ExportResponse Shape

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "requested_by": "uuid",
  "format": "dxf",
  "status": "queued",
  "source_job_id": "uuid | null",
  "progress_percent": 0,
  "retry_count": 0,
  "errors": null,
  "artifact_file_id": "uuid | null",
  "compliance_record_id": "uuid | null",
  "idempotency_key": "string",
  "metadata": {},
  "error_message": null,
  "bucket": null,
  "file_path": null,
  "created_at": "2026-06-04T00:00:00Z",
  "updated_at": "2026-06-04T00:00:00Z"
}
```

---

## Notes

- Server always sets `status=queued`, `progress_percent=0`, `requested_by` on creation
- worker calls `PATCH /exports/{id}/status` to update lifecycle
- Frontend reads `GET /exports/project/{project_id}` for export history
- `idempotency_key` prevents duplicate export requests
- Pipeline stages go in `metadata.stage`, not as DB status columns
