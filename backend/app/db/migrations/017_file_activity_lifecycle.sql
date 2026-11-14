BEGIN;

ALTER TABLE public.files
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'files_version_positive'
          AND conrelid = 'public.files'::regclass
    ) THEN
        ALTER TABLE public.files
            ADD CONSTRAINT files_version_positive CHECK (version > 0) NOT VALID;
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_files_project_version
    ON public.files(project_id, version DESC);

COMMIT;
