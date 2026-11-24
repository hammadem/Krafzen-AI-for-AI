BEGIN;
CREATE TABLE IF NOT EXISTS public.bim_model_validations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  file_id uuid NOT NULL REFERENCES public.files(id) ON DELETE RESTRICT,
  created_by uuid NOT NULL REFERENCES auth.users(id),
  source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  result jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS bim_model_validation_file_history_idx
ON public.bim_model_validations(project_id,file_id,created_by,created_at DESC);
ALTER TABLE public.bim_model_validations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.bim_model_validations FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON public.bim_model_validations TO service_role;
COMMENT ON TABLE public.bim_model_validations IS 'Owner-scoped bounded source IFC diagnostic evidence; not full model validity or professional approval.';
NOTIFY pgrst, 'reload schema';
COMMIT;
