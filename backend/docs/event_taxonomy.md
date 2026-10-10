# Event Taxonomy — KRAFZEN AI
Owner: Tazwar
Branch: feat/week1-kiruthika-architecture-foundation

Event namespaces and payload samples for queue/worker/notification systems.
All events emitted by worker_service.py and activity_service.py.

---

## Audit event contract

`activity_events` is the append-only audit store. Its canonical fields are:
`event_id`, `organization_id`, `actor_user_id`, `action`, `entity_type`,
`entity_id`, `project_id`, `timestamp`, and `metadata`. `organization_id`
references a workspace; `entity_id` is intentionally polymorphic so event
records survive deletion of the referenced entity. `timestamp` is stored as
UTC `timestamptz`.

The table retains `id`, `event_name`, `job_id`, and `created_at` as compatibility
columns. The shared activity service writes both shapes, and API responses
include both canonical audit fields and legacy activity-feed aliases.
`export.*` events use `entity_type="export_job"` and the existing
`export_jobs.id` as `entity_id`.

Audit rows cannot be directly updated, deleted, or truncated. Foreign-key
cleanup may null relationship columns when a referenced workspace, project,
user, or export job is deleted; the audit event, action, timestamp, and generic
entity reference remain. Normal application users have read-only access;
inserts are performed by the backend service role. Historical events are not
assigned to a workspace automatically because projects do not currently have
a workspace relationship; those events remain available in project activity.

### Standard action names

| Entity | Actions |
|---------|---------|
| `file` | `file.uploaded`, `file.updated`, `file.renamed`, `file.version_created`, `file.exported`, `file.archived`, `file.restored`, `file.deleted` |
| `ai_review` | `ai.review_started`, `ai.review_completed`, `ai.review_failed` |
| `ai_generation` | `ai.generation_started`, `ai.generation_completed`, `ai.generation_failed` |
| `ai_suggestion` | `ai.suggestion_accepted`, `ai.suggestion_rejected` |
| `revision` | `revision.created`, `revision.approved`, `revision.rejected`, `revision.restored` |
| `member` | `member.invited`, `member.joined`, `member.removed`, `member.role_changed` |
| `permission` | `permission.changed` |

Use `file.renamed` only when its display name changes; use `file.updated` for
other file metadata changes. `file.exported` records inclusion of a file in an
export. Emit `file.deleted` in the same transaction as a hard deletion (before
removing the file row), or after the soft-delete state change commits. The
event's generic entity reference is not a file foreign key, so deletion will
not cascade to its audit history. Export-job lifecycle actions (`export.queued`, `export.processing`,
`export.validating`, `export.completed`, `export.failed`, and
`export.requires_review`) remain supported for compatibility with the current
worker.

Action values are text rather than a database enum so new actions can be added
without a schema migration. Event names describe completed actions or state
changes, not commands that have yet to run.

---

## Namespaces

| Namespace       | Owner   | Description                              |
|-----------------|---------|------------------------------------------|
| `project.*`     | Yehor   | Project CRUD lifecycle                   |
| `file.*`        | Yehor   | File upload, delete, rename              |
| `export.*`      | Tazwar  | Export job lifecycle (worker-emitted)    |
| `validation.*`  | Kiruthika | Compliance/preflight/postflight results |
| `notification.*`| Tazwar  | In-app notification delivery             |

---

## `export.*`

Emitted by `worker_service.emit_export_event()` → persisted via `activity_service.record_event()`.

| Event                    | Trigger                                      |
|--------------------------|----------------------------------------------|
| `export.queued`          | Job created at QUEUED status                 |
| `export.processing`      | Worker advances job to PROCESSING            |
| `export.validating`      | Worker advances job to VALIDATING            |
| `export.completed`       | Worker advances job to COMPLETED             |
| `export.failed`          | Any failure path in worker                   |
| `export.requires_review` | Postflight sets requires_review=True         |

### Sample payload — `export.completed`
```json
{
  "event_name": "export.completed",
  "job_id": "aaaaaaaa-0000-0000-0000-000000000001",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "actor_user_id": "cccccccc-0000-0000-0000-000000000003",
  "message": "Export completed",
  "metadata": {
    "source": "worker",
    "format": "dxf",
    "stage": "export_generation"
  },
  "created_at": "2026-06-05T14:30:00Z"
}
```

### Sample payload — `export.failed`
```json
{
  "event_name": "export.failed",
  "job_id": "aaaaaaaa-0000-0000-0000-000000000001",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "actor_user_id": "cccccccc-0000-0000-0000-000000000003",
  "message": "Export timed out.",
  "metadata": {
    "source": "worker",
    "error": "Export timed out after processing stage"
  },
  "created_at": "2026-06-05T14:31:00Z"
}
```

---

## `project.*`

Owned by Yehor. Documented here for cross-team reference.

| Event             | Trigger                        |
|-------------------|--------------------------------|
| `project.created` | POST /api/v1/projects          |
| `project.updated` | PATCH /api/v1/projects/{id}    |
| `project.deleted` | DELETE /api/v1/projects/{id}   |

### Sample payload — `project.created`
```json
{
  "event_name": "project.created",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "actor_user_id": "cccccccc-0000-0000-0000-000000000003",
  "metadata": {
    "input_text": "3 bedroom IRC-compliant layout"
  },
  "created_at": "2026-06-05T14:00:00Z"
}
```

---

## `file.*`

Owned by Yehor. Tazwar wires these into activity feed in Week 3 Step 3.

| Event           | Trigger                   |
|-----------------|---------------------------|
| `file.uploaded` | File stored in Supabase   |
| `file.deleted`  | File removed              |
| `file.renamed`  | File metadata updated     |
| `upload.failed` | Storage write failed      |

### Sample payload — `file.uploaded`
```json
{
  "event_name": "file.uploaded",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "actor_user_id": "cccccccc-0000-0000-0000-000000000003",
  "metadata": {
    "file_id": "dddddddd-0000-0000-0000-000000000004",
    "file_type": "dxf",
    "bucket": "dxf-files",
    "path": "cccccccc-0000-0000-0000-000000000003/bbbbbbbb-0000-0000-0000-000000000002/project_bb_20260605_143000.dxf"
  },
  "created_at": "2026-06-05T14:30:05Z"
}
```

---

## `validation.*`

Owned by Kiruthika. Results surface via `export_validation_service.py`.

| Event                      | Trigger                              |
|----------------------------|--------------------------------------|
| `validation.preflight_pass`| Preflight gate passes                |
| `validation.preflight_fail`| Preflight blocks job (can_proceed=False) |
| `validation.postflight_pass`| Postflight passes (passed=True)     |
| `validation.postflight_fail`| Postflight fails (passed=False)     |
| `validation.review_required`| requires_review=True after postflight|

### Sample payload — `validation.preflight_fail`
```json
{
  "event_name": "validation.preflight_fail",
  "job_id": "aaaaaaaa-0000-0000-0000-000000000001",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "metadata": {
    "issues": [
      {
        "code": "EXPORT_MISSING_PROJECT",
        "severity": "error",
        "message": "Export requires a project_id.",
        "category": "export_integrity"
      }
    ],
    "checked_at_stage": "validation_precheck"
  },
  "created_at": "2026-06-05T14:29:58Z"
}
```

---

## `notification.*`

Owned by Tazwar. Delivered via `notification_service.create_notification()`.

| Type                       | Trigger                          |
|----------------------------|----------------------------------|
| `export_completed`         | Worker reaches COMPLETED         |
| `export_failed`            | Worker reaches FAILED            |
| `export_requires_review`   | Postflight requires_review=True  |
| `validation_update`        | Validation result available      |

### Sample payload — `export_completed` notification
```json
{
  "user_id": "cccccccc-0000-0000-0000-000000000003",
  "type": "export_completed",
  "message": "Your export is ready.",
  "job_id": "aaaaaaaa-0000-0000-0000-000000000001",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "is_read": false,
  "created_at": "2026-06-05T14:30:01Z"
}
```

---

## Storage Path Ack (T6)
Reviewed `backend/docs/storage-architecture.md`.
Confirmed alignment on CAD file path convention:
`dxf-files/{user_id}/{project_id}/{filename}`

Worker artifact handoff flow (from storage-architecture.md):
1. Export job completes → `StorageService.upload_cad_file()` uploads to `dxf-files` bucket
2. Returns public URL → `PATCH /projects/{project_id}` with `{ "dxf_url": "..." }`
3. Yehor's API saves URL to project record
4. Sunny reads `dxf_url` and shows download button

No conflicts with queue/worker ownership. Ack — Tazwar.