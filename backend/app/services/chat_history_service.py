from typing import List, Dict, Any, Optional
from app.db.supabase_client import db
import logging

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """
    Service to manage persistent chat history in Supabase.
    """
    
    async def create_session(self, user_id: str, title: str = "New Chat") -> str:
        """Creates a new chat session and returns its ID."""
        try:
            data = {
                "user_id": user_id,
                "title": title
            }
            response = db.table("chat_sessions").insert(data).execute()
            if response.data:
                return response.data[0]["id"]
            raise Exception("Failed to create chat session")
        except Exception as e:
            logger.error(f"Error creating chat session: {e}", exc_info=True)
            raise e

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all chat sessions for a user, ordered by recent update."""
        try:
            # Order by updated_at descending
            response = db.table("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching sessions: {e}")
            return []

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves all messages for a specific session, with feedback attached."""
        try:
            response = db.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
            messages = response.data or []
            if not messages:
                return []
            message_ids = [m["id"] for m in messages]
            feedback_map = await self._get_feedback_for_message_ids(message_ids)
            for m in messages:
                m["feedback"] = feedback_map.get(m["id"])
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    async def _get_feedback_for_message_ids(self, message_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Returns a map of message_id -> { reaction, reason } for the given message IDs."""
        if not message_ids:
            return {}
        try:
            response = db.table("message_feedback").select("message_id, reaction, reason").in_("message_id", message_ids).execute()
            return {row["message_id"]: {"reaction": row["reaction"], "reason": row.get("reason")} for row in (response.data or [])}
        except Exception as e:
            logger.error(f"Error fetching feedback: {e}")
            return {}

    async def message_belongs_to_user(self, message_id: str, user_id: str) -> bool:
        """Check that the message exists and its session belongs to the user."""
        try:
            msg = db.table("chat_messages").select("session_id").eq("id", message_id).limit(1).execute()
            if not msg.data:
                return False
            session_id = msg.data[0]["session_id"]
            sessions = await self.get_user_sessions(user_id)
            return any(s["id"] == session_id for s in sessions)
        except Exception as e:
            logger.error(f"Error checking message ownership: {e}")
            return False

    async def upsert_feedback(self, message_id: str, user_id: str, reaction: str, reason: Optional[str] = None) -> bool:
        """Set or update feedback for a message. Returns True on success."""
        if reaction not in ("up", "down"):
            return False
        if not await self.message_belongs_to_user(message_id, user_id):
            return False
        try:
            from datetime import datetime
            now = datetime.now().isoformat()
            row = {"message_id": message_id, "reaction": reaction, "reason": reason, "updated_at": now}
            db.table("message_feedback").upsert(row, on_conflict="message_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting feedback: {e}", exc_info=True)
            return False

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        image_url: Optional[str] = None,
        compliance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Adds a message to a session. Optional ``compliance`` stores IRC screening JSON on assistant rows."""
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "image_url": image_url,
            }
            if compliance is not None:
                data["compliance"] = compliance
            response = db.table("chat_messages").insert(data).execute()
            
            # Update session's updated_at timestamp
            from datetime import datetime
            db.table("chat_sessions").update({"updated_at": datetime.now().isoformat()}).eq("id", session_id).execute()
            
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error adding message: {e}", exc_info=True)
            raise e

    async def get_or_create_recent_session(self, user_id: str) -> str:
        """
        Gets the most recent session or creates a new one if none exist or if requested.
        For simplicity, we'll just get the latest one.
        """
        sessions = await self.get_user_sessions(user_id)
        if sessions:
            return sessions[0]["id"]
        return await self.create_session(user_id)

    async def update_session_title(self, session_id: str, user_id: str, title: str) -> bool:
        """Updates the title of a chat session."""
        try:
            # Verify ownership first
            sessions = await self.get_user_sessions(user_id)
            if not any(s['id'] == session_id for s in sessions):
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return False
            
            # Update the title
            from datetime import datetime
            response = db.table("chat_sessions").update({
                "title": title,
                "updated_at": datetime.now().isoformat()
            }).eq("id", session_id).execute()
            
            return response.data is not None
        except Exception as e:
            logger.error(f"Error updating session title: {e}", exc_info=True)
            raise e

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Deletes a chat session."""
        try:
            # RLS policies should ideally handle user_id check, but we add explicit check here
            response = db.table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
            if not response.data:
                # If no data returned, it implies session didn't exist or wasn't owned by user
                return False
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            raise e

chat_history_service = ChatHistoryService()
