CREATE TABLE IF NOT EXISTS public.exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE, -- export belongs to a job
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  requested_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, -- who triggered the export
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN (
    'queued', --export request created, waiting to be picked up
    'processing', 
    'validating',-- file generated, running validation checks
    'completed', -- export ready, file available for download
    'failed',-- something went wrong
    'requires_review'-- needs manual review before completing
  )),
  file_path TEXT,-- path to the exported file in storage
  bucket TEXT,-- storage bucket name
  format TEXT,-- e.g. dxf, pdf, ifc
  error_message TEXT, -- populated if status is failed
  metadata JSONB, -- TO BE FIXED
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);