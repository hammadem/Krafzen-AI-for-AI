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
DROP POLICY IF EXISTS "Users view own projects" ON projects;
CREATE POLICY "Users view own projects" ON projects FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users insert own projects" ON projects;
CREATE POLICY "Users insert own projects" ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Jobs policies
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own jobs" ON jobs;
CREATE POLICY "Users view own jobs" ON jobs FOR ALL USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
DROP POLICY IF EXISTS "Users insert own jobs" ON jobs;
CREATE POLICY "Users insert own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));

-- Files policies (FIXED: job_id instead of file_id)
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own files" ON files;
CREATE POLICY "Users view own files" ON files FOR ALL USING (auth.uid() = (SELECT user_id FROM jobs j JOIN projects p ON j.project_id = p.id WHERE j.id = files.job_id));
DROP POLICY IF EXISTS "Users insert own files" ON files;
CREATE POLICY "Users insert own files" ON files FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM jobs j JOIN projects p ON j.project_id = p.id WHERE j.id = files.job_id));


-- Link Supabase Auth Users to Public Profile/Subscription
-- Note: 'auth.users' is a system table. We track extra data in 'user_subscriptions'
CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    stripe_customer_id TEXT,
    plan_tier TEXT DEFAULT 'free', -- 'free', 'pro'
    remaining_minutes FLOAT DEFAULT 100.0,
    total_minutes_purchased FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to create user_subscription on new user signup
-- This function needs to run as SECURITY DEFINER to access auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_subscriptions (user_id, remaining_minutes)
  VALUES (new.id, 100.0)
  ON CONFLICT (user_id) DO NOTHING; -- Idempotency
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger execution
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Chat Sessions (Threads)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    image_url TEXT, -- For user uploaded images
    tokens_used INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payment History
CREATE TABLE IF NOT EXISTS payment_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_session_id TEXT,
    amount_paid INTEGER, -- In cents
    minutes_added INTEGER,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for new tables
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own subscription" ON user_subscriptions;
CREATE POLICY "Users view own subscription" ON user_subscriptions FOR SELECT USING (auth.uid() = user_id);
-- Only system can update subscriptions usually, but if we need frontend to update? No, backend updates.

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own sessions" ON chat_sessions;
CREATE POLICY "Users view own sessions" ON chat_sessions FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users insert own sessions" ON chat_sessions;
CREATE POLICY "Users insert own sessions" ON chat_sessions FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users update own sessions" ON chat_sessions;
CREATE POLICY "Users update own sessions" ON chat_sessions FOR UPDATE USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users delete own sessions" ON chat_sessions;
CREATE POLICY "Users delete own sessions" ON chat_sessions FOR DELETE USING (auth.uid() = user_id);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own messages" ON chat_messages;
CREATE POLICY "Users view own messages" ON chat_messages FOR SELECT USING (auth.uid() = (SELECT user_id FROM chat_sessions WHERE id = session_id));
DROP POLICY IF EXISTS "Users insert own messages" ON chat_messages;
CREATE POLICY "Users insert own messages" ON chat_messages FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM chat_sessions WHERE id = session_id));

ALTER TABLE payment_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own payments" ON payment_history;
CREATE POLICY "Users view own payments" ON payment_history FOR SELECT USING (auth.uid() = user_id);