BEGIN;

DROP POLICY IF EXISTS "Users view activity for own projects or workspaces"
    ON public.activity_events;
CREATE POLICY "Users view activity for own projects or workspaces"
    ON public.activity_events
    FOR SELECT
    USING (
        auth.uid() = (
            SELECT projects.user_id
            FROM public.projects
            WHERE projects.id = activity_events.project_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.workspaces
            WHERE workspaces.id = COALESCE(
                activity_events.organization_id,
                activity_events.workspace_id
            )
              AND workspaces.owner_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1
            FROM public.workspace_members
            WHERE workspace_members.workspace_id = COALESCE(
                activity_events.organization_id,
                activity_events.workspace_id
            )
              AND workspace_members.user_id = auth.uid()
        )
    );

REVOKE ALL PRIVILEGES
    ON TABLE public.activity_events
    FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT
    ON TABLE public.activity_events
    TO service_role;
GRANT SELECT
    ON TABLE public.activity_events
    TO authenticated;

COMMIT;
