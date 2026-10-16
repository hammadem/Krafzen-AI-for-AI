# Event Taxonomy — KRAFZEN AI
Owner: Tazwar
Branch: feat/week1-kiruthika-architecture-foundation

Event namespaces and payload samples for queue/worker/notification systems.
All events emitted by worker_service.py and activity_service.py.

---

## Namespaces

| Namespace       | Owner   | Description                              |
|-----------------|---------|------------------------------------------|
| `project.*`     | Yehor   | Project CRUD lifecycle                   |
| `file.*`        | Yehor   | File upload, delete, rename              |
| `export.*`      | Tazwar  | Export job lifecycle (worker-emitted)    |
| `validation.*`  | Kiruthika | Compliance/preflight/postflight results |
| `notification.*`| Tazwar  | In-app notification delivery             |
| `team.*`        | KRAFZEN | Workspace membership and role lifecycle |
| `permissions.*` | KRAFZEN | Workspace access and role permission changes |

---

## Workspace team and permissions

Workspace events are stored in `activity_events` with `workspace_id` set.
Their `actor_user_id` is always taken from the authenticated JWT subject
(`require_auth`); target user IDs and invite tokens are never used as the actor.

| Event | Trigger |
|---|---|
| `team.member_invited` | An owner creates an invitation |
| `team.member_joined` | The invited user accepts using an authenticated account whose email matches the invitation |
| `team.member_removed` | An owner removes a member |
| `team.role_changed` | An owner changes a member's role |
| `permissions.access_granted` | An invitation is accepted and workspace membership is created |
| `permissions.access_revoked` | An invitation is revoked or an active member is removed |
| `permissions.permission_changed` | A member's workspace role is changed |

Role-change events include `target_user_id`, `from_role`, and `to_role` in
metadata. Membership and access events include the target user or invitation
email and the role involved. A no-op role update does not produce a change event.

Invite acceptance endpoint: `POST /api/v1/workspaces/invites/accept` with
`{"token": "<invite token>"}` and a valid bearer token for the invited user.
The server verifies the account email against the invitation before creating
membership or recording the join event.

The authenticated global activity feed at `GET /api/v1/dashboard/activity`
combines activity events for the user's projects and workspaces with export
status events. Each event includes an ID, category, actor, project (when
applicable), message, timestamp, and metadata. Category values used by the
Activity UI are `files`, `ai`, `revisions`, `team`, `permissions`, and `exports`.

File activity is available at `GET /api/v1/activity/files/{file_id}`. The caller
must own the file's project; the response combines events linked to that file
with lifecycle events for its job. File creation, rename, and deletion events
store the file ID, project ID, job ID, and authenticated actor ID. New AI,
revision, approval, and export actions that belong to a particular file should
also persist its `file_id` to `activity_events`.

Authenticated users have read-only access to `activity_events`. Audit event
inserts are performed by trusted backend services; clients cannot insert,
update, or delete event rows. Project events are visible only to the project
owner, and workspace events only to the workspace owner or current members.
Deleting a project detaches its activity rows instead of cascading their
deletion; detached events remain readable only to their original actor.

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