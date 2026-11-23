-- Private scanned photographs linked to actual field observations.
create table if not exists public.field_photos (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    inspection_id uuid not null references public.field_inspections(id) on delete cascade,
    created_by uuid not null references auth.users(id),
    bucket text not null,
    path text not null unique,
    mime_type text not null check (mime_type = 'image/jpeg'),
    size_bytes bigint not null check (size_bytes between 1 and 10485760),
    source_metadata jsonb not null,
    created_at timestamptz not null default now()
);
create index if not exists field_photos_inspection_owner
    on public.field_photos (inspection_id, created_by, created_at desc);
alter table public.field_photos enable row level security;
revoke all on public.field_photos from PUBLIC, anon, authenticated;
grant all on public.field_photos to service_role;
comment on table public.field_photos is
'Private, ClamAV scanned, re-encoded EXIF/GPS stripped photos from user field observations; no automatic defect verification.';
