-- IFC import metadata (requires deployment before enabling /files/import-ifc).
-- Data is generated server-side by IfcOpenShell, never supplied by the client.
ALTER TABLE public.files
  ADD COLUMN IF NOT EXISTS import_metadata jsonb;

COMMENT ON COLUMN public.files.import_metadata IS
  'Validated IFC schema, project identifiers and entity counts; not certified geometry';
