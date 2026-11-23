-- Project-owned audit trail for evidence-only IFC AABB broad-phase screening.
-- These are candidate bounding-box intersections, not confirmed hard clashes.
-- Roll out only after applying and testing the prerequisite IFC/schema migrations.
CREATE TABLE IF NOT EXISTS public.bim_spatial_screenings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    primary_file_id uuid NOT NULL REFERENCES public.files(id) ON DELETE RESTRICT,
    secondary_file_id uuid NOT NULL REFERENCES public.files(id) ON DELETE RESTRICT,
    created_by uuid NOT NULL REFERENCES auth.users(id),
    alignment_user_asserted boolean NOT NULL DEFAULT false
        CHECK (alignment_user_asserted = true),
    result jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT bim_spatial_screenings_distinct_files
        CHECK (primary_file_id <> secondary_file_id)
);
CREATE INDEX IF NOT EXISTS bim_spatial_screenings_project_created_at_idx
    ON public.bim_spatial_screenings (project_id, created_by, created_at DESC);
ALTER TABLE public.bim_spatial_screenings ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.bim_spatial_screenings FROM PUBLIC, anon, authenticated;
GRANT ALL ON public.bim_spatial_screenings TO service_role;
COMMENT ON TABLE public.bim_spatial_screenings IS
'Persisted source IFC triangle AABB overlap candidates. Requires aligned model origins/axes/scale, qualified review, and does NOT establish hard clashes.';
