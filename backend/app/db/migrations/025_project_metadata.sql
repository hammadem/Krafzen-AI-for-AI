-- Add optional metadata without rewriting existing project prompts or assets.
BEGIN;
ALTER TABLE public.projects
  ADD COLUMN IF NOT EXISTS title text CHECK (title IS NULL OR (char_length(title) BETWEEN 1 AND 160 AND btrim(title) <> '')),
  ADD COLUMN IF NOT EXISTS description text CHECK (description IS NULL OR char_length(description) <= 8000),
  ADD COLUMN IF NOT EXISTS project_type text CHECK (project_type IS NULL OR project_type IN ('residential','commercial','industrial','institutional','infrastructure','mixed_use','other')),
  ADD COLUMN IF NOT EXISTS lifecycle_stage text NOT NULL DEFAULT 'draft' CHECK (lifecycle_stage IN ('draft','in_progress','in_review','completed'));
CREATE INDEX IF NOT EXISTS projects_owner_type_stage_idx ON public.projects (user_id, project_type, lifecycle_stage, created_at DESC) WHERE archived_at IS NULL;
NOTIFY pgrst, 'reload schema';
COMMIT;
