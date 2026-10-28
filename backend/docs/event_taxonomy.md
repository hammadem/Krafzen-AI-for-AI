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
export. `file.deleted` is recorded before hard-deleting the file row; its generic
entity reference is not a file foreign key, so deletion will not cascade to its
audit history. Export-job lifecycle actions (`export.queued`, `export.processing`,
`export.validating`, `export.completed`, `export.failed`, and
`export.requires_review`) remain supported for compatibility with the current
worker.

Action values are text rather than a database enum so new actions can be added
without a schema migration. Event names describe completed actions or state
changes, not commands that have yet to run.

AI audit metadata contains lifecycle references and non-content attributes
such as IDs, jurisdiction, stage, and exception class. Prompts, generated CAD
content, image URLs, and raw exception messages must not be copied into audit
rows. Suggestion decisions reference the assistant message ID and are accepted
only for an assistant message owned by the authenticated user.

Revision events are emitted for versioned `files` rows. The file UUID is the
revision reference, `version` identifies its human-facing version, and approval
state is persisted on that row. Approve/reject and restore events are written
only after the corresponding file state update succeeds. Restoring a revision
means unarchiving that version; it does not overwrite or duplicate stored file
content.

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

Workspace events are stored in `activity_events` with both `workspace_id` and
the legacy `organization_id` set to the workspace UUID.
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
metadata. Membership and access events include target user or invitation identifiers and
the role involved. New invitation events do not persist invitation email
addresses or tokens in audit metadata. A no-op role update does not produce a
change event.

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

Emitted by `worker_service.emit_export_event()` → persisted via
`activity_service.record_audit_event()`.

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

File-row creation records `file.uploaded`; a new row explicitly created with a
version greater than 1 also records `file.version_created`. File metadata edits
record `file.renamed` when the display name changes and `file.updated` for
other changed fields. Archive/restore endpoints record the corresponding state
transition. Export artifacts record `file.exported` when saved through the
artifact-file persistence helper.

Every event uses `entity_type="file"` and includes file ID, display name, file
type, version, project ID, and actor user ID in metadata. The canonical event
columns separately store actor, project, and UTC timestamp. Apply
`012_file_activity_lifecycle.sql` and `014_file_revision_approval.sql` before
using version, archive, or revision approval behavior.

| Event                  | Trigger                                      |
|------------------------|----------------------------------------------|
| `file.uploaded`        | File row successfully created                |
| `file.updated`         | Non-name file metadata changed               |
| `file.renamed`         | Display name changed                         |
| `file.version_created`| File row created with version greater than 1|
| `file.exported`        | Export artifact persisted                    |
| `file.archived`        | File moved to archived state                 |
| `file.restored`        | Archived file restored                       |
| `file.deleted`         | File row hard-deleted                        |

### Sample payload — `file.uploaded`
```json
{
  "event_name": "file.uploaded",
  "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
  "actor_user_id": "cccccccc-0000-0000-0000-000000000003",
  "metadata": {
    "file_id": "dddddddd-0000-0000-0000-000000000004",
    "file_name": "project_bb_20260605_143000.dxf",
    "file_type": "dxf",
    "file_id": "dddddddd-0000-0000-0000-000000000004",
    "version": 1,
    "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
    "user_id": "cccccccc-0000-0000-0000-000000000003"
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