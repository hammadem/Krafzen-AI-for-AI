-- Match the authenticated file service's actual private-storage contract.
-- Preserve legacy URLs as historical data, never infer private storage paths from them.
BEGIN;
ALTER TABLE public.files
  ADD COLUMN IF NOT EXISTS project_id uuid REFERENCES public.projects(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS bucket text,
  ADD COLUMN IF NOT EXISTS path text,
  ADD COLUMN IF NOT EXISTS mime_type text,
  ADD COLUMN IF NOT EXISTS size_bytes bigint,
  ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS archived_at timestamptz,
  ADD COLUMN IF NOT EXISTS approval_state text NOT NULL DEFAULT 'pending_review',
  ADD COLUMN IF NOT EXISTS reviewed_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS reviewed_at timestamptz;
ALTER TABLE public.files ALTER COLUMN file_url DROP NOT NULL;
-- Only the backend registers or modifies storage references. Existing ownership
-- policies remain for authorized reads. Service role operations remain available.
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.files FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.files TO service_role;
CREATE INDEX IF NOT EXISTS files_active_job_idx ON public.files(job_id) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS files_project_idx ON public.files(project_id);
NOTIFY pgrst, 'reload schema';
COMMIT;
