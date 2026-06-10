CREATE TABLE IF NOT EXISTS public.export_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  requested_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  source_job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL, -- optional, originating job
  format TEXT NOT NULL CHECK (format IN ('dxf', 'ifc', 'dwg', 'revit_package')),
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN (
    'queued',           -- export created, waiting to be picked up
    'processing',       -- worker is generating the file
    'validating',       -- file generated, running validation
    'completed',        -- export ready
    'failed',           -- something went wrong
    'requires_review',  -- needs manual review
    'cancelled'         -- export was cancelled
  )),
  progress_percent INTEGER NOT NULL DEFAULT 0,   -- 0-100, updated by Tazwar's worker
  retry_count INTEGER NOT NULL DEFAULT 0,        -- how many times worker retried
  errors JSONB,                                  -- error details if failed
  artifact_file_id UUID,                         -- file id once export is complete
  compliance_record_id UUID,                     -- set by Kiruthika's contracts system
  compliance_preset_id TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,          -- prevents duplicate export requests
  metadata JSONB NOT NULL DEFAULT '{}',          -- stage, preset_id, artifact_urls etc
  error_code TEXT,
  error_message TEXT,                            -- human readable error
  bucket TEXT,                                   -- storage bucket
  file_path TEXT,                                -- path to exported file
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);