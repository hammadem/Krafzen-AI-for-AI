# Audit Trail Architecture

## Scope and status

This document describes the audit activity implementation and its current
operational boundaries. It is an implementation snapshot, not evidence that
the production database migration or export generation has been deployed.

## Components and event flow

1. Authenticated route handlers derive the acting user and authorize access to
   the workspace, project, job, or file.
2. Backend services call `record_audit_event` or a typed helper such as
   `record_file_event`. The writer records the actor, action, entity, optional
   project/file context, and non-sensitive metadata in `activity_events`.
3. Workspace identity is written to both canonical `workspace_id` and legacy
   `organization_id` fields. Migration 016 synchronizes existing rows and
   future inserts while retaining compatibility with older readers.
4. Read services return bounded, stably ordered event windows. Workspace,
   project, and file reads apply their scope identifiers; file history also
   includes compatible job-level legacy events that do not identify a
   different file or revision.
5. Dashboard APIs expose offset pagination and `has_more`. The global and
   project activity pages append pages of 50 records and suppress duplicate
   event IDs. File activity reports errors with a retry action.

## Storage and compatibility

`activity_events` contains canonical event fields such as `event_id`, `action`,
`entity_type`, `entity_id`, `timestamp`, `file_id`, and `workspace_id`, as well
as legacy fields used by existing producers and readers. Event retrieval uses
stable timestamp and identifier tie-breakers. The existing append-only trigger
is preserved; migration 016 temporarily drops and recreates it around the
backfill and installs a before-insert synchronization trigger.

The migration runner applies the existing 015 migration and new 016 migration
after earlier explicitly ordered migrations. It requires the documented
database URL, `psql`, backup confirmation, and interactive operator approval.
The migration has not been applied to a live database as part of this work.

## Privacy and authorization

Audit records use authenticated actor IDs and scoped resource identifiers.
Invitation email addresses and invite tokens are excluded from newly written
invitation audit metadata. Chat prompts and generated image URLs are not
included in AI audit metadata, and the chat route does not log prompt text or
image URLs. The chat transcript itself is stored by the chat-history feature;
that is separate from the audit trail.

Service-role database access does not replace authorization. Routes must
authorize workspace/project membership before querying scoped audit events.
File history is accessed only after the file route verifies access to the
requested file.

## Export provenance

Export postflight requires an `artifact_file_id` before an export can be marked
completed. The current `run_export_generation()` implementation is a stub and
does not create or persist an artifact, so this gate intentionally prevents a
false-success status. A real artifact generator, job-to-artifact linkage,
retry/idempotency behavior, and end-to-end provenance remain future work.

## Known operational boundaries

- File mutations and audit writes are separate database requests, not one
  transaction. The API reports an audit-write failure explicitly, but cannot
  reliably roll back a completed file mutation.
- Migration trigger behavior, append-only enforcement, row-level security, and
  workspace compatibility must be verified against a database environment.
- Pagination is offset-based. The maximum backend offset and the deployed
  PostgREST row cap should be reviewed together for large datasets.
- Export completion remains blocked until artifact generation is implemented.
