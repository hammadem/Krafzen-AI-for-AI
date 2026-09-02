-- Migration 010: Index chat messages by (session_id, created_at DESC) for fast paginated chat loading.

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created 
ON chat_messages (session_id, created_at DESC);
