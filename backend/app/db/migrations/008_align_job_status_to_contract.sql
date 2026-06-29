-- Migration 001: Align jobs.status to export-lifecycle contract
-- Required because schema.sql uses legacy values: pending/transcribing/parsing/generating
-- Contract source of truth: /api/v1/contracts/export-lifecycle (ExportStatus enum)

-- job_model.py and schema.sql both use status values (pending, transcribing, parsing, generating)
-- that are not in ExportStatus. Per instructions, I'm raising this before implementing.
-- I'll fix the model + add a migration. Please confirm no live Supabase rows with legacy statuses
-- before I merge the SQL.

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_status_check;

ALTER TABLE jobs
    ALTER COLUMN status SET DEFAULT 'queued',
    ADD CONSTRAINT jobs_status_check CHECK (
        status IN ('queued', 'processing', 'validating', 'requires_review', 'completed', 'failed', 'cancelled')
    );

-- Migrate any legacy rows to their nearest contract equivalent
UPDATE jobs SET status = 'queued'     WHERE status = 'pending';
UPDATE jobs SET status = 'processing' WHERE status IN ('transcribing', 'parsing', 'generating', 'running');
-- 'completed' and 'failed' already match; no row should have 'cancelled' yet