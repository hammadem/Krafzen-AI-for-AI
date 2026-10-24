import logging

from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.supabase_client import db

logger = logging.getLogger(__name__)

async def get_user_email(user_id: str) -> dict:
    """Fetch user profile including email from Supabase Auth."""
    
    email = None
    try:
        user_response = db.auth.admin.get_user_by_id(user_id)
        email = getattr(user_response.user, 'email', None)
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Failed to fetch email for user {user_id}: {e}")
    
    return {"email": email}