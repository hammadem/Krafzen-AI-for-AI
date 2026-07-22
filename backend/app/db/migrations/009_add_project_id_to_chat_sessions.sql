--add_project_id_to_chat_sessions.sql
ALTER TABLE chat_sessions
  ADD COLUMN IF NOT EXISTS project_id uuid REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id
  ON chat_sessions(project_id);