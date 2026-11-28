-- Persist real drawing-linked review markups; backend enforces owned file and project.
create table if not exists public.drawing_redlines (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    file_id uuid not null references public.files(id) on delete cascade,
    file_version integer not null default 1,
    created_by uuid not null references auth.users(id),
    kind text not null check (kind in ('comment','line','arrow','rectangle','highlight')),
    x double precision not null check (x between 0 and 1),
    y double precision not null check (y between 0 and 1),
    x2 double precision check (x2 between 0 and 1),
    y2 double precision check (y2 between 0 and 1),
    comment text not null check (length(comment) between 1 and 2000),
    severity text not null check (severity in ('info','low','medium','high','critical')),
    status text not null default 'open' check (status in ('open','resolved')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists drawing_redlines_file_time_idx
on public.drawing_redlines (file_id, created_at desc);
alter table public.drawing_redlines enable row level security;
revoke all on public.drawing_redlines from PUBLIC, anon, authenticated;
grant all on public.drawing_redlines to service_role;
comment on table public.drawing_redlines is
'Version-bound DXF coordinates normalized to preview viewport; observations not engineering approvals.';
