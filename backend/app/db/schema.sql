-- Supabase schema definition (Provisional for Weeks 1-2)
-- Designed/Validated by: Laxmi Pranitha Muskula
-- Notes: Users via Supabase Auth; RLS for security; JSONB for parsed AI output

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table (voice/text inputs)
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    parsed_json JSONB,
    dxf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table (workflow status: transcribe/parse/generate)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'transcribing', 'parsing', 'generating', 'completed', 'failed')),
    transcript TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files table (DXF storage)
CREATE TABLE IF NOT EXISTS files (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_type TEXT DEFAULT 'dxf',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies (Basic Auth - Expand for Full Layers)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own projects" ON projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own projects" ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Similar for jobs/files
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own jobs" ON jobs FOR ALL USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users insert own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));

ALTER TABLE files ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own files" ON files FOR ALL USING (auth.uid() = (SELECT user_id FROM jobs j JOIN projects p ON j.project_id = p.id WHERE j.id = file_id));
CREATE POLICY "Users insert own files" ON files FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM jobs j JOIN projects p ON j.project_id = p.id WHERE j.id = file_id));
