-- Week 1 architecture foundations (Kiruthika lead scope)
-- Adds compliance/jurisdiction domain entities + export job tracking model.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Canonical jurisdiction registry
CREATE TABLE IF NOT EXISTS jurisdictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    jurisdiction_id TEXT NOT NULL UNIQUE, -- ex: US_IRC_BASELINE
    label TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'draft')),
    schema_version INT NOT NULL DEFAULT 1,
    supported_exports JSONB NOT NULL DEFAULT '["dxf","ifc","dwg"]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compliance preset catalog per jurisdiction/version
CREATE TABLE IF NOT EXISTS compliance_presets (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    preset_id TEXT NOT NULL UNIQUE, -- ex: us-irc-baseline-v1
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(jurisdiction_id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    default_approval_state TEXT NOT NULL DEFAULT 'pending_review'
        CHECK (default_approval_state IN ('pending_review', 'approved', 'rejected')),
    rule_version TEXT NOT NULL, -- ex: us_irc_baseline@1
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rule metadata catalog (execution engine can reference these in later phases)
CREATE TABLE IF NOT EXISTS compliance_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    preset_id TEXT NOT NULL REFERENCES compliance_presets(preset_id) ON DELETE CASCADE,
    rule_code TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'geometry', 'dimension', 'zoning', 'occupancy', 'structure', 'export_integrity'
    )),
    severity TEXT NOT NULL CHECK (severity IN ('warning', 'error', 'critical')),
    description TEXT NOT NULL,
    rule_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(preset_id, rule_code)
);

-- Project-level compliance snapshots and approval lifecycle
CREATE TABLE IF NOT EXISTS project_compliance_records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    preset_id TEXT NOT NULL REFERENCES compliance_presets(preset_id) ON DELETE RESTRICT,
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(jurisdiction_id) ON DELETE RESTRICT,
    rule_version TEXT NOT NULL,
    status_label TEXT NOT NULL, -- good/needs_review/not_compliant/insufficient_data
    approval_state TEXT NOT NULL DEFAULT 'pending_review'
        CHECK (approval_state IN ('pending_review', 'approved', 'rejected')),
    score_percent NUMERIC(5,2),
    validation_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reviewed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exception/audit records for manual overrides and tracked rationale
CREATE TABLE IF NOT EXISTS compliance_exceptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    compliance_record_id UUID NOT NULL REFERENCES project_compliance_records(id) ON DELETE CASCADE,
    exception_code TEXT NOT NULL,
    reason TEXT NOT NULL,
    raised_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    approval_state TEXT NOT NULL DEFAULT 'pending_review'
        CHECK (approval_state IN ('pending_review', 'approved', 'rejected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Export jobs (separate from existing jobs table; designed for queued export lifecycle)
CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    requested_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    format TEXT NOT NULL CHECK (format IN ('dxf', 'ifc', 'dwg', 'revit_package')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN (
        'queued', 'processing', 'validating', 'requires_review', 'completed', 'failed', 'cancelled'
    )),
    progress_percent INT NOT NULL DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    retry_count INT NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    artifact_file_id UUID REFERENCES files(id) ON DELETE SET NULL,
    compliance_record_id UUID REFERENCES project_compliance_records(id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    queued_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_export_jobs_project_status ON export_jobs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_export_jobs_requested_by ON export_jobs(requested_by);
CREATE INDEX IF NOT EXISTS idx_project_compliance_project ON project_compliance_records(project_id);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_preset ON compliance_rules(preset_id);

