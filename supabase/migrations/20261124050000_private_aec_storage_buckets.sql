-- KRAFZEN source-bound CAD/BIM imports default to private bucket dxf-files.
-- This migration provisions the missing bucket without moving existing objects.
-- The existing US regional bucket has 2 items and must not expose customer
-- engineering files through publicly guessable object URLs.
-- Storage still uses service-role backend endpoints with explicit project ACL.
BEGIN;
INSERT INTO storage.buckets (id,name,public,file_size_limit)
VALUES ('dxf-files','dxf-files',false,52428800)
ON CONFLICT (id) DO UPDATE SET
  public = false,
  file_size_limit = 52428800;
UPDATE storage.buckets
   SET public=false
 WHERE id='krafzen-us-files' AND public IS DISTINCT FROM false;
COMMIT;
