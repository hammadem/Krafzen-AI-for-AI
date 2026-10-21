-- 1. Organization Branding Assets Tracking Table
CREATE TABLE IF NOT EXISTS branding_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    storage_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_hash TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_branding_assets_org ON branding_assets(organization_id);

-- 2. Schema Migration Audit Logs
CREATE TABLE IF NOT EXISTS branding_migration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'branding_version',
    source_version_id UUID NOT NULL,
    from_schema_version TEXT NOT NULL,
    to_schema_version TEXT NOT NULL,
    migrated_configuration JSONB NOT NULL,
    applied_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);