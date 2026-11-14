-- Migration: Create reports storage bucket and access policies

-- 1. Create or register the 'reports' bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'reports',
    'reports',
    false, -- Private bucket: access requires signed URLs
    20971520, -- 20 MB limit
    ARRAY['application/pdf', 'application/dxf']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 20971520,
    allowed_mime_types = ARRAY['application/pdf', 'application/dxf'];

-- 2. Allow service-role access to upload, read, and sign URLs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Service Role Access Reports'
    ) THEN
        CREATE POLICY "Service Role Access Reports"
        ON storage.objects FOR ALL
        TO service_role
        USING (bucket_id = 'reports')
        WITH CHECK (bucket_id = 'reports');
    END IF;
END $$;