BEGIN;

ALTER TABLE public.files
    ADD COLUMN IF NOT EXISTS approval_state TEXT NOT NULL DEFAULT 'pending_review',
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'files_approval_state_valid'
          AND conrelid = 'public.files'::regclass
    ) THEN
        ALTER TABLE public.files
            ADD CONSTRAINT files_approval_state_valid
            CHECK (approval_state IN ('pending_review', 'approved', 'rejected')) NOT VALID;
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_files_project_approval
    ON public.files(project_id, approval_state, version DESC);

COMMIT;
