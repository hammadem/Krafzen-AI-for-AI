# Week 1 Supabase Migration Runbook

**Owner:** Kiruthika only — do not run on shared DB without team notice.

## Order

Run in Supabase SQL editor or CLI, in order:

1. `supabase/migrations/20260507183000_projects_add_image_and_dwg_urls.sql`
2. `backend/app/db/migrations/001_align_job_status_to_contract.sql`
3. `backend/app/db/migrations/002_week1_architecture_foundations.sql`
4. `backend/app/db/migrations/003_workspace_tables.sql` — optional if accepting workspace on shared DB

## Pre-checks

- Backup or confirm staging window with team.
- No interns run migrations on production/shared project.

## Post-checks

```sql
-- columns exist
SELECT column_name FROM information_schema.columns
WHERE table_name = 'projects' AND column_name IN ('image_url', 'dwg_url');

-- export_jobs exists
SELECT COUNT(*) FROM export_jobs;

-- job statuses are contract values only
SELECT DISTINCT status FROM jobs;
```

## Smoke test (after migrations)

1. Login → create project → chat/DXF flow unchanged.
2. `GET /api/v1/contracts/export-lifecycle` returns 7 states.
3. Dashboard activity loads without 500.

## Rollback

Do not drop tables on shared DB without CEO approval. Prefer forward-fix migrations.
