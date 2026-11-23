-- Persistent, owner-bound evidence for conservative DXF as-built comparisons.
-- Server-side API verifies file ownership before storage reads; customer roles
-- cannot write comparison records directly through PostgREST.
create table if not exists public.asbuilt_comparisons (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    original_file_id uuid not null references public.files(id) on delete restrict,
    revised_file_id uuid not null references public.files(id) on delete restrict,
    created_by uuid not null references auth.users(id),
    result jsonb not null,
    created_at timestamptz not null default now(),
    constraint asbuilt_distinct_revisions check (original_file_id <> revised_file_id)
);

create index if not exists asbuilt_comparisons_project_user_time
on public.asbuilt_comparisons (project_id, created_by, created_at desc);

alter table public.asbuilt_comparisons enable row level security;
revoke all on public.asbuilt_comparisons from PUBLIC, anon, authenticated;
grant all on public.asbuilt_comparisons to service_role;

comment on table public.asbuilt_comparisons is
'Stored exact-coordinate DXF difference evidence; not physical as-built certification.';
