CREATE TABLE IF NOT EXISTS public.residency_audit_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,                  -- e.g. "organization_residency.activated"
    region_code VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_residency_audit_org_created 
ON public.residency_audit_events(organization_id, created_at DESC);

-- Enable RLS
ALTER TABLE public.residency_audit_events ENABLE ROW LEVEL SECURITY;

-- Allow workspace members (or admins) to view audit events
CREATE POLICY "Allow members to view residency audit events"
ON public.residency_audit_events
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.workspace_members wm
        WHERE wm.workspace_id = residency_audit_events.organization_id
          AND wm.user_id = auth.uid()
    )
);

-- Service role full access
CREATE POLICY "Allow service_role full management on residency_audit_events"
ON public.residency_audit_events
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);