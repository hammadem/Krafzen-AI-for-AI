-- Migration 008: Align jobs.status to export-lifecycle contract
-- Required because schema.sql uses legacy values: pending/transcribing/parsing/generating
-- Contract source of truth: /api/v1/contracts/export-lifecycle (ExportStatus enum)

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_status_check;

-- Migrate legacy rows FIRST while there is no constraint
UPDATE jobs SET status = 'queued'     WHERE status = 'pending';
UPDATE jobs SET status = 'processing' WHERE status IN ('transcribing', 'parsing', 'generating', 'running');
-- 'completed' and 'failed' already match; no row should have 'cancelled' yet

-- Now add the new constraint — all rows already comply
ALTER TABLE jobs
    ALTER COLUMN status SET DEFAULT 'queued',
    ADD CONSTRAINT jobs_status_check CHECK (
        status IN ('queued', 'processing', 'validating', 'requires_review', 'completed', 'failed', 'cancelled')
    );