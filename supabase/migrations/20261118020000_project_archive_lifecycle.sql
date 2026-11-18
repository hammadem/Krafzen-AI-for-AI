-- Document Modules 1/2: durable project archive/restore, no file deletion.
-- Apply only to isolated staging after reviewing prior migrations.
ALTER TABLE public.projects
  ADD COLUMN IF NOT EXISTS archived_at timestamptz,
  ADD COLUMN IF NOT EXISTS archived_by uuid,
  ADD COLUMN IF NOT EXISTS restored_at timestamptz,
  ADD COLUMN IF NOT EXISTS restored_by uuid;
CREATE INDEX IF NOT EXISTS idx_projects_owner_archive_created
  ON public.projects (user_id, archived_at, created_at DESC);
COMMENT ON COLUMN public.projects.archived_at
  IS 'Null for active projects, timestamp for archived projects; archive never deletes documents';
COMMENT ON COLUMN public.projects.archived_by
  IS 'Authenticated user who most recently archived the project';
COMMENT ON COLUMN public.projects.restored_at
  IS 'Most recent restoration time';
COMMENT ON COLUMN public.projects.restored_by
  IS 'Most recent restoration actor';
