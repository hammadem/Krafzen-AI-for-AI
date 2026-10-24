"""
Supabase service for database operations
"""


from httpx import HTTPError
from postgrest.exceptions import APIError
from supabase import Client, create_client

from app.core.config import settings
from app.utils.logger import logger


class SupabaseService:
    """Handles Supabase client initialization and basic operations"""

    def __init__(self):
        self.client: Client | None = None
        self.init_client()

    def init_client(self):
        """Initialize Supabase client"""
        try:
            # Use the Service Role Key for backend operations (higher privileges)
            url = getattr(settings, "SUPABASE_URL", None)
            key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None) or getattr(settings, "SUPABASE_KEY", None)

            if not url or not key:
                # Only log at debug level to reduce noise in test environments
                logger.debug("Missing Supabase credentials (SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY). This is expected in test environments.")
                self.client = None
                return

            self.client = create_client(url, key)
            logger.info("Supabase client initialized successfully")

        except (HTTPError, OSError, TypeError, ValueError) as e:
            logger.error("Error initializing Supabase client", error=str(e), exc_info=True)
            self.client = None

    def is_connected(self) -> bool:
        """Check if Supabase client is initialized"""
        return self.client is not None

    def test_connection(self) -> dict:
        """Quick connectivity check"""
        if not self.client:
            return {
                "status": "error",
                "message": "Supabase client not initialized",
                "connected": False
            }

        try:
            # Perform a lightweight query on an existing table
            response = self.client.table("projects").select("id").limit(1).execute()
            connected = response is not None
            return {
                "status": "success" if connected else "warning",
                "message": "Supabase connection successful" if connected else "Supabase responded but no data found",
                "connected": connected
            }

        except (APIError, HTTPError) as e:
            return {
                "status": "error",
                "message": f"Supabase connection failed: {e!s}",
                "connected": False
            }


# Global instance (auto-initialized on import)
supabase_service = SupabaseService()
