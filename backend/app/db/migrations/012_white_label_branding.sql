-- Phase 3.2: White-Label Branding Schema

-- 1. branding_drafts: Working draft per organization with optimistic locking
CREATE TABLE IF NOT EXISTS public.branding_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'draft', -- 'draft', 'publishing', 'discarded'
    revision INT NOT NULL DEFAULT 1,
    restored_from_version_id UUID,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_branding_drafts_org UNIQUE (organization_id)
);

-- 2. branding_versions: Immutable published snapshots
CREATE TABLE IF NOT EXISTS public.branding_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    configuration JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'published', -- 'published', 'archived'
    published_by UUID,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_draft_id UUID,
    restored_from_version_id UUID,
    configuration_hash VARCHAR(64) NOT NULL,
    schema_version VARCHAR(32) NOT NULL DEFAULT 'v1',
    CONSTRAINT uq_branding_version_org_num UNIQUE (organization_id, version_number)
);

-- 3. branding_audit_events: Append-only event history
CREATE TABLE IF NOT EXISTS public.branding_audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    actor_id UUID,
    event_type VARCHAR(64) NOT NULL, -- 'draft.updated', 'branding.published', 'draft.discarded', 'draft.restored'
    resource_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Efficient query indexes
CREATE INDEX IF NOT EXISTS idx_branding_drafts_org ON public.branding_drafts(organization_id);
CREATE INDEX IF NOT EXISTS idx_branding_versions_org_num ON public.branding_versions(organization_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_branding_audit_org_time ON public.branding_audit_events(organization_id, created_at DESC);