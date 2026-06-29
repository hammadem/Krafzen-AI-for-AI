-- 006_exports.sql
-- Refactored: export_jobs is already created by 002_week1_architecture_foundations.sql.
-- This migration ADDS the columns 006 originally introduced, via ALTER (no CREATE TABLE),
-- to avoid the duplicate-CREATE conflict on deploy.

BEGIN;

-- New columns 002 did not define
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS errors JSONB;
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS compliance_preset_id TEXT;
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS bucket TEXT;
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS file_path TEXT;

-- idempotency_key: added NULLABLE (cannot add NOT NULL to a table with existing rows).
-- Uniqueness enforced via a separate unique index below.
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS uq_export_jobs_idempotency_key
    ON public.export_jobs (idempotency_key);

-- Columns the reviewer listed that 002 ALREADY defines — included with IF NOT EXISTS
-- so this migration is self-documenting and safe (these are no-ops if present).
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS error_code TEXT;
ALTER TABLE public.export_jobs ADD COLUMN IF NOT EXISTS error_message TEXT;

COMMIT;