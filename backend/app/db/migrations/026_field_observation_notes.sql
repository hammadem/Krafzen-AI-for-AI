BEGIN;
CREATE TABLE IF NOT EXISTS public.field_observation_notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  inspection_id uuid NOT NULL REFERENCES public.field_inspections(id) ON DELETE CASCADE,
  created_by uuid NOT NULL REFERENCES auth.users(id),
  kind text NOT NULL CHECK (kind IN ('comment','corrective_action','progress_update')),
  body text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 4000 AND btrim(body) <> ''),
  due_date date,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (due_date IS NULL OR kind = 'corrective_action')
);
CREATE INDEX IF NOT EXISTS field_observation_notes_inspection_idx
 ON public.field_observation_notes(inspection_id,created_at,id);
ALTER TABLE public.field_observation_notes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.field_observation_notes FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.field_observation_notes TO service_role;
NOTIFY pgrst, 'reload schema';
COMMIT;
