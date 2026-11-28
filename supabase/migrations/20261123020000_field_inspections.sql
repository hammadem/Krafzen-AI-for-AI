-- Evidence-backed field observations, no pretend photos or field reports.
-- API uses service-role behind authenticated project ownership checks.
create table if not exists public.field_inspections (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    created_by uuid not null references auth.users(id),
    title text not null check (char_length(title) between 3 and 180),
    description text not null check (char_length(description) between 1 and 4000),
    location_label text check (char_length(location_label) <= 250),
    discipline text not null check (discipline in ('architecture','structural','mechanical','electrical','plumbing','site','other')),
    severity text not null check (severity in ('low','medium','high','critical')),
    status text not null default 'open' check (status in ('open','in_progress','resolved','verified')),
    observed_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    resolved_at timestamptz
);
create index if not exists field_inspections_project_time_idx
    on public.field_inspections (project_id, created_at desc);
alter table public.field_inspections enable row level security;
revoke all on public.field_inspections from PUBLIC, anon, authenticated;
grant all on public.field_inspections to service_role;
comment on table public.field_inspections is
'Actual project-linked field observations; status requires human action; not automatic code compliance certification.';
