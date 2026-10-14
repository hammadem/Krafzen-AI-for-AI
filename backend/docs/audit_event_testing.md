# Reusable audit event service and safe manual test

## Record an event from backend code

New callers should use the canonical helper in
`app/services/activity_service.py`:

```python
from app.services.activity_service import record_audit_event

event = await record_audit_event(
    actor_user_id=user_id,       # None for an automated/system event
    organization_id=workspace_id,  # None when the action is not workspace-scoped
    project_id=project_id,       # None when the action is not project-scoped
    action="file.renamed",
    entity_type="file",
    entity_id=file_id,
    metadata={"old_name": "plan.dxf", "new_name": "floor-plan.dxf"},
)
```

The helper generates `event_id` and a UTC `timestamp`, writes both canonical
audit fields and legacy activity-feed columns, and returns the stored row.
Database errors are logged and re-raised; callers must not treat a failed
insert as a successful event. The old `record_event(...)` entry point remains
available for existing call sites.

## Verify automatic file activity in staging

Apply migrations `010_activity_events_audit_contract.sql`,
`011_file_activity_lifecycle.sql`, and `012_file_revision_approval.sql` to staging. Upload a file through the
application, then copy its file ID from the response or file record and run:

```sql
SELECT
    event_id,
    actor_user_id,
    project_id,
    action,
    entity_type,
    entity_id,
    "timestamp" AT TIME ZONE 'UTC' AS timestamp_utc,
    metadata
FROM public.activity_events
WHERE entity_type = 'file'
  AND entity_id = '<file-uuid>'
ORDER BY "timestamp";
```

The upload should have a `file.uploaded` row with the same file ID, actor, and
project. The event metadata should include `file_id`, `file_name`, `file_type`,
`version`, `project_id`, and `user_id`; `timestamp_utc` should match the upload
time. Renaming the file should append `file.renamed` with `old_name` and
`new_name`, and archiving/restoring it should append `file.archived` and
`file.restored`. No event is written for a failed file-row operation.

## Manually generate three test events

Use a **staging** Supabase project, never production. These events are
append-only and will remain in the database; the test marker makes them easy to
identify but they cannot be removed through the application.

1. Apply migrations `010_activity_events_audit_contract.sql`,
   `011_file_activity_lifecycle.sql`, and `012_file_revision_approval.sql` to staging first.
2. In the backend environment, make sure `SUPABASE_URL` and
   `SUPABASE_SERVICE_ROLE_KEY` point to that staging project. Do not paste or
   commit the service-role key.
3. Use real UUIDs for a user, a project owned by that user, a file linked via
   its job to that project, and (optionally) a workspace the user belongs to.
4. From the `backend` directory, preview first:

   ```powershell
   python scripts\generate_audit_test_events.py `
     --actor-user-id <user-uuid> `
     --project-id <project-uuid> `
     --entity-id <file-uuid>
   ```

   Add `--organization-id <workspace-uuid>` if the events should be workspace
   scoped. Preview mode makes no database calls and writes nothing.
5. After checking that the configured Supabase host is the staging project,
   run the same command with `--write`. The script checks project ownership,
   verifies the file's job belongs to the project, optionally verifies
   workspace membership, then asks you to type `APPEND TEST EVENTS`.
6. Save the printed **Audit test run ID**. The script inserts
   `file.updated`, `file.renamed`, and `file.exported`, reads each row back, and
   checks actor, workspace, project, action, entity type/id, UTC timestamp, and
   the run marker.

Example with workspace:

```powershell
python scripts\generate_audit_test_events.py `
  --actor-user-id 00000000-0000-0000-0000-000000000001 `
  --project-id 00000000-0000-0000-0000-000000000002 `
  --entity-id 00000000-0000-0000-0000-000000000003 `
  --organization-id 00000000-0000-0000-0000-000000000004 `
  --write
```

## Independently inspect the stored rows

In the Supabase SQL editor for staging, replace `<run-id>` with the ID printed
by the script:

```sql
SELECT
    event_id,
    actor_user_id,
    organization_id,
    project_id,
    action,
    entity_type,
    entity_id,
    "timestamp" AT TIME ZONE 'UTC' AS timestamp_utc,
    metadata
FROM public.activity_events
WHERE metadata ->> 'audit_test_run_id' = '<run-id>'
ORDER BY (metadata ->> 'sequence')::integer;
```

Expected result: three rows, in order, with your selected actor/workspace/
project/file IDs and the actions `file.updated`, `file.renamed`, and
`file.exported`. `timestamp_utc` should be close to the time you ran the script.
The rename row also contains the old and new names in metadata.

The manual script exercises the real staging database. The unit tests under
`app/tests/test_activity_service.py` and `app/tests/test_file_activity.py` use
fake database responses and are safe for routine local runs, but do not prove
that a Supabase migration has been applied.
