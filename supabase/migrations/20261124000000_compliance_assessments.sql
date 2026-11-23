-- Persist reviewable, source-linked numerical ADA screening evidence.
-- Provider-facing service_role is only intended reader/writer; no public grants.
create table if not exists public.compliance_assessments (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    source_file_id uuid references public.files(id) on delete restrict,
    created_by uuid not null references auth.users(id),
    jurisdiction jsonb not null,
    measurements jsonb not null,
    result jsonb not null,
    review_status text not null default 'pending_qualified_review'
        check (review_status in ('pending_qualified_review','reviewed','rejected')),
    created_at timestamptz not null default now()
);
create index if not exists compliance_assessments_project_owner_time_idx
    on public.compliance_assessments (project_id, created_by, created_at desc);
alter table public.compliance_assessments enable row level security;
revoke all on public.compliance_assessments from PUBLIC, anon, authenticated;
grant all on public.compliance_assessments to service_role;
comment on table public.compliance_assessments is
'User-declared ADA 2010 numeric measurement screening only; never an authority approval or full code compliance finding.';
