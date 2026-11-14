ALTER TABLE public.activity_events
    ADD COLUMN IF NOT EXISTS file_id UUID;

CREATE INDEX IF NOT EXISTS idx_activity_file_created_at
    ON public.activity_events(file_id, created_at DESC);

ALTER TABLE public.activity_events
    DROP CONSTRAINT IF EXISTS activity_events_project_id_fkey;

ALTER TABLE public.activity_events
    ADD CONSTRAINT activity_events_project_id_fkey
    FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;

ALTER TABLE public.activity_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Actors view orphaned activity" ON public.activity_events;
CREATE POLICY "Actors view orphaned activity" ON public.activity_events
    FOR SELECT USING (
        project_id IS NULL
        AND workspace_id IS NULL
        AND actor_user_id = auth.uid()
    );

REVOKE ALL PRIVILEGES ON TABLE public.activity_events FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.activity_events TO authenticated;
GRANT ALL PRIVILEGES ON TABLE public.activity_events TO service_role;
