# Day 10 QA Report — Audit Trail & Activity Log

**Sprint duration:** 10 working days  
**Developer:** Alisa  
**Technical reviewer:** Kiruthika  
**Backend/security review:** Hammad  
**Product review:** Khadija  
**Execution date:** 2026-10-28  
**Overall result:** **INCOMPLETE — automated regression checks pass, but Day 10 end-to-end and live-database sign-off is not complete.**

## Executive summary

The local automated backend and frontend checks passed. The backend audit-focused
regression selection passed **51 tests**, and the complete backend suite passed
**150 tests**. Frontend tests passed (**19 tests across 11 files**), TypeScript
checking passed, and lint completed with **0 errors and 55 warnings**.

These results establish unit and mocked-service behavior, not the complete
Day 10 user journeys. A manual drawing-generation attempt against the
backend-configured **production Supabase project** failed before AI generation:
PostgREST reported `PGRST204` because the `activity_events.file_id` column was
missing from its schema cache. No production migration was run during QA.
Live migration/RLS/trigger verification and the team workflow were not
completed. Export generation also remains a stub, so a fully successful
file-to-export provenance journey cannot currently be signed off.

## Results by the sprint's 10 QA areas

| # | Area | Result | Test execution and evidence | Remaining gap |
|---|---|---|---|---|
| 1 | File events | **PARTIAL** | Backend tests cover upload, rename/update, version creation, archive/restore, delete, export-source references, event metadata, and actor attribution. The audit-focused suite passed 51 tests. | The complete manual create-project → upload DWG → rename → version → export flow was not run against a live database. Export generation is still a stub. |
| 2 | AI events | **FAIL (production)** | Unit tests cover suggestion acceptance/rejection references and generation-failure audit metadata. The manual drawing attempt failed before image generation when writing `ai.generation_started`: PostgREST returned `PGRST204`, reporting that `activity_events.file_id` was missing from the schema cache. | Have the database owner review and apply the required schema migration through the production change process, then verify the schema and rerun AI generation and the review → revision → approval flow. Do not retry against production until the audit schema is fixed. |
| 3 | Revision events | **PARTIAL** | Unit tests cover revision creation, review, approval, and restore event behavior, including reviewer/approver attribution and the requirement to review before approval. | No full AI-to-revision-to-approval workflow or live persistence check was run. |
| 4 | Team events | **NOT VERIFIED** | Existing tests exercise activity-event shaping and display of a membership event, but that is not an invitation/join/role/access/removal workflow test. | Invite → join → role change → project access → removal was not tested. No direct team/permission event lifecycle result is available. |
| 5 | Permissions | **PARTIAL** | Backend security tests cover denial of private-project activity to another user, denial of workspace activity to non-members/removed members, and file-access checks before reading file history. Upload audit tests verify the actor comes from the authenticated user rather than a request-supplied ID. | These are mocked/unit checks. Cross-organization behavior and the full removed-user access flow were not verified against a live database. |
| 6 | Activity UI | **PARTIAL** | Frontend test run passed **19 tests in 11 files**. Existing coverage includes activity pagination and file-activity rendering. TypeScript check passed. | The sprint's complete filter set (event type, user, project, date) and search behavior were not confirmed as an end-to-end UI scenario. |
| 7 | File history | **PARTIAL** | Tests cover merging canonical and legacy file/job events, excluding unrelated file/project events, duplicate-free results, ordering, and access checks. | No live file-history journey was run from upload through export, and database-backed history was not verified. |
| 8 | Project history | **PARTIAL** | Dashboard/project activity tests cover scoping and a synthetic 1,000-event timeline with no page gaps or duplicate events. | Project history was not verified against a deployed database or through a manual project-level UI flow. |
| 9 | Performance | **PARTIAL** | Automated pagination exercised a synthetic 1,000-event history without gaps or duplicates. | No measured latency, concurrent-load, 100-event baseline, or 10,000+ event test was run. Deployed PostgREST row caps and offset limits remain unverified. |
| 10 | Security | **PARTIAL** | Unit tests verify application-level authorization gates and actor attribution. Audit metadata tests check that sensitive prompt/content fields are omitted. | Live RLS, grants, append-only protections, migration trigger/backfill behavior, and multi-user/org isolation were not tested. These must be verified in staging before security sign-off. |

## Test execution evidence

Commands were run on the local development checkout on 2026-10-28. Frontend
commands were run from the `frontend` directory.

| Check | Command | Result |
|---|---|---|
| Audit-focused backend regression | `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_activity_service.py backend\app\tests\test_dashboard.py backend\app\tests\test_file_activity.py backend\app\tests\test_file_activity_security.py backend\tests\unit\test_export_validation_service.py backend\tests\unit\test_worker_service.py backend\tests\unit\test_production_entrypoint.py -q` | **Passed: 51 tests** |
| Complete backend test suite | `backend\.venv\Scripts\python.exe -m pytest -q` | **Passed: 150 tests; 0 failures; 43 warnings** |
| Frontend tests | `npm.cmd test -- --run` | **Passed: 11 files, 19 tests** |
| TypeScript check | `npx.cmd tsc --noEmit` | **Passed** |
| Frontend lint | `npm.cmd run lint -- --no-cache` | **Completed: 0 errors, 55 warnings** |

The backend tests use mocked database responses for the audit paths described
above. A passing unit suite does not establish that migrations or database
policies are active in staging or production. The manual AI attempt is live
failure evidence from the production project configured in the backend.

## Open sign-off items

1. In **staging**, apply the documented audit migrations and verify workspace
   backfill/synchronization, append-only behavior, grants, and RLS. For
   production, use the database owner's reviewed migration and backup process;
   do not run the broad Week 2 migration script as an ad hoc fix.
2. Run the five Day 10 manual scenarios in staging: file lifecycle, AI/revision
   chain, team lifecycle, unauthorized access attempts, and large-history
   pagination. Record test identities/data without including credentials.
3. Before claiming file-provenance completion, implement and exercise real
   export artifact creation and persistence; the current completion gate
   intentionally blocks success without a linked artifact.
4. Measure performance at 100 and 1,000 events and, if practical, 10,000+
   events. Record response times and confirm deployed row/offset limits.
5. Re-run the staging checks after deployment and update each **PARTIAL** or
   **NOT VERIFIED** row with its environment, execution evidence, and final
   pass/fail result.

**Release recommendation:** Do not use this report as final production
sign-off. The automated checks are green, but the live database, manual
end-to-end flows, and performance targets remain outstanding.
