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
        """Retrieves all messages for a specific session."""
        try:
            response = db.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    async def add_message(self, session_id: str, role: str, content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Adds a message to a session."""
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "image_url": image_url
            }
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

chat_history_service = ChatHistoryService()
