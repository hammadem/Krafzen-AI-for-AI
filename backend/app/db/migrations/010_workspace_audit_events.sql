ALTER TABLE public.activity_events
    ADD COLUMN IF NOT EXISTS workspace_id UUID;

CREATE INDEX IF NOT EXISTS idx_activity_workspace_created_at
    ON public.activity_events(workspace_id, created_at DESC);

DROP POLICY IF EXISTS "Workspace members view workspace activity" ON public.activity_events;
CREATE POLICY "Workspace members view workspace activity" ON public.activity_events
    FOR SELECT USING (
        workspace_id IS NOT NULL
        AND (
            EXISTS (
                SELECT 1
                FROM public.workspaces
                WHERE workspaces.id = activity_events.workspace_id
                  AND workspaces.owner_id = auth.uid()
            )
            OR EXISTS (
                SELECT 1
                FROM public.workspace_members
                WHERE workspace_members.workspace_id = activity_events.workspace_id
                  AND workspace_members.user_id = auth.uid()
            )
        )
    );
