"""
Supabase service for database operations
"""

from supabase import create_client, Client
from app.core.config import settings
from typing import Optional


class SupabaseService:
    """Handles Supabase client initialization and basic operations"""

    def __init__(self):
        self.client: Optional[Client] = None
        self.init_client()

    def init_client(self):
        """Initialize Supabase client"""
        try:
            # Use the Service Role Key for backend operations (higher privileges)
            url = getattr(settings, "SUPABASE_URL", None)
            key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None) or getattr(settings, "SUPABASE_KEY", None)

            if not url or not key:
                print("⚠️  Warning: Missing Supabase credentials (SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY).")
                self.client = None
                return

            self.client = create_client(url, key)
            print("✅ Supabase client initialized successfully.")

        except Exception as e:
            print(f"❌ Error initializing Supabase client: {e}")
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

        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase connection failed: {str(e)}",
                "connected": False
            }


# 🔹 Global instance (auto-initialized on import)
supabase_service = SupabaseService()
