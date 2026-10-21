DO $$ BEGIN
    CREATE TYPE residency_status_enum AS ENUM (
        'provisioning',
        'active',
        'failed',
        'suspended'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS public.organization_residency (
    organization_id  UUID PRIMARY KEY REFERENCES public.workspaces(id) ON DELETE CASCADE,
    region_code      VARCHAR(32) NOT NULL,
    status           residency_status_enum NOT NULL DEFAULT 'provisioning',
    assigned_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by      UUID NOT NULL REFERENCES auth.users(id),
    last_verified_at TIMESTAMPTZ,
    policy_version   VARCHAR(32) NOT NULL DEFAULT 'v1.0',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org_residency_region_status 
ON public.organization_residency (region_code, status);

ALTER TABLE public.organization_residency ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow workspace members to read organization residency"
ON public.organization_residency
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.workspace_members wm
        WHERE wm.workspace_id = organization_residency.organization_id
          AND wm.user_id = auth.uid()
    )
);

CREATE POLICY "Allow workspace admins to manage organization residency"
ON public.organization_residency
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.workspace_members wm
        WHERE wm.workspace_id = organization_residency.organization_id
          AND wm.user_id = auth.uid()
          AND wm.role IN ('owner', 'admin')
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.workspace_members wm
        WHERE wm.workspace_id = organization_residency.organization_id
          AND wm.user_id = auth.uid()
          AND wm.role IN ('owner', 'admin')
    )
);

CREATE POLICY "Allow service_role full management on organization_residency"
ON public.organization_residency
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);