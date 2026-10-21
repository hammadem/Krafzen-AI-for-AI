-- report_branding_snapshots
CREATE TABLE IF NOT EXISTS public.report_branding_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    report_id UUID NOT NULL,
    branding_version_id UUID REFERENCES public.branding_versions(id) ON DELETE RESTRICT,
    template_version_id VARCHAR(100) NOT NULL,
    configuration_hash VARCHAR(64) NOT NULL,
    schema_version VARCHAR(20) NOT NULL DEFAULT 'v1',
    applied_configuration JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Indexes for rapid lookup by tenant, report, and version
CREATE INDEX IF NOT EXISTS idx_report_branding_snapshots_org_id 
    ON public.report_branding_snapshots(organization_id);

CREATE INDEX IF NOT EXISTS idx_report_branding_snapshots_report_id 
    ON public.report_branding_snapshots(report_id);

CREATE INDEX IF NOT EXISTS idx_report_branding_snapshots_branding_version_id 
    ON public.report_branding_snapshots(branding_version_id);