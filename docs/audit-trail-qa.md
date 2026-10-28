# Audit Trail QA

## Result

Audit-trail and export-gate regression checks pass. The full backend suite is
not green: 147 tests passed and one unrelated Dodo payment test failed during
execution. Frontend tests, type checking, and lint completed successfully.
Database deployment and live RLS/trigger behavior remain unverified.

## Verification evidence

Commands were run from the repository root unless noted otherwise.

| Check | Command | Result |
|---|---|---|
| Audit, activity, file, export, worker, and production-entrypoint tests | `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_activity_service.py backend\app\tests\test_dashboard.py backend\app\tests\test_file_activity.py backend\app\tests\test_file_activity_security.py backend\tests\unit\test_export_validation_service.py backend\tests\unit\test_worker_service.py backend\tests\unit\test_production_entrypoint.py -q` | Passed: 49 tests |
| Full backend suite | `backend\.venv\Scripts\python.exe -m pytest -q` | 147 passed, 1 failed. `backend/tests/unit/test_dodo_payments.py::test_handle_dodo_webhook_does_not_resolve_user_id_from_customer_email` fails because it patches `payment_service_module.db`, which is not an attribute of `payment_service`. This is outside the audit-trail changes. |
| Frontend tests (from `frontend`) | `npm.cmd test -- --run` | Passed: 11 files, 19 tests |
| TypeScript (from `frontend`) | `npx.cmd tsc --noEmit` | Passed |
| Frontend lint (from `frontend`) | `npm.cmd run lint -- --no-cache` | Passed with 0 errors and 55 warnings |
| Ruff on changed Python files | `backend\.venv\Scripts\python.exe -m ruff check backend\main.py backend\app\main.py backend\app\routes\activity_routes.py backend\app\routes\chat_routes.py backend\app\routes\dashboard_routes.py backend\app\services\activity_service.py backend\app\services\export_validation_service.py backend\app\db\queries\invite_queries.py backend\app\db\queries\job_queries.py backend\app\tests\test_activity_service.py backend\app\tests\test_dashboard.py backend\app\tests\test_file_activity.py backend\app\tests\test_file_activity_security.py backend\tests\unit\test_export_validation_service.py backend\tests\unit\test_worker_service.py backend\tests\unit\test_production_entrypoint.py` | Passed |
| Python compilation | `backend\.venv\Scripts\python.exe -m compileall -q backend\main.py backend\app backend\tests` | Passed |
| Whitespace/error check | `git diff --check` | Passed |

## Coverage exercised

- Activity writer validation, workspace alias writes/reads, canonical and
  legacy file-history merging, and stable bounded ordering.
- Project/workspace/file activity isolation and paginated dashboard behavior,
  including a synthetic 1,000-event timeline with no page gaps or duplicates.
- File mutation audit failure reporting and safe audit references.
- Exports without an artifact are blocked from successful postflight and
  completion.
- The production `uvicorn main:app` compatibility entry point exports the
  canonical FastAPI application.
- Frontend activity pagination and file activity rendering.

## Not verified / remaining

- Migration 016 was not applied to a live database. Its backfill, insert
  synchronization trigger, append-only protection, database grants, and RLS
  must be verified in the target database environment using the documented
  migration procedure.
- No live multi-user authorization or database-backed integration test was
  run.
- Pagination is offset-based; verify the deployed PostgREST row cap and the
  configured offset bound against expected data volume.
- Export generation remains a stub without artifact creation or persistence.
  The missing-artifact gate prevents false completion, but actual artifact
  provenance and retry/idempotency are not implemented.
- File mutation and audit insertion are separate requests, so an audit-store
  failure is surfaced but cannot guarantee rollback of the mutation.
