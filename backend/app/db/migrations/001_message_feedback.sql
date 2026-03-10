-- Message feedback (thumbs up/down per generated image)
-- Run this on existing DBs that already have chat_messages.

CREATE TABLE IF NOT EXISTS message_feedback (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    reaction TEXT NOT NULL CHECK (reaction IN ('up', 'down')),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(message_id)
);

ALTER TABLE message_feedback ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own message feedback" ON message_feedback;
CREATE POLICY "Users view own message feedback" ON message_feedback FOR SELECT USING (auth.uid() = (SELECT user_id FROM chat_sessions WHERE id = (SELECT session_id FROM chat_messages WHERE id = message_id)));
DROP POLICY IF EXISTS "Users insert own message feedback" ON message_feedback;
CREATE POLICY "Users insert own message feedback" ON message_feedback FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM chat_sessions WHERE id = (SELECT session_id FROM chat_messages WHERE id = message_id)));
DROP POLICY IF EXISTS "Users update own message feedback" ON message_feedback;
CREATE POLICY "Users update own message feedback" ON message_feedback FOR UPDATE USING (auth.uid() = (SELECT user_id FROM chat_sessions WHERE id = (SELECT session_id FROM chat_messages WHERE id = message_id)));
