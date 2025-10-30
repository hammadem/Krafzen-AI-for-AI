"""
Supabase service for database operations
"""

from supabase import create_client, Client
from app.core.config import settings
from typing import Optional

class SupabaseService:
    """Supabase database service"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            if settings.SUPABASE_URL and settings.SUPABASE_KEY:
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            else:
                print("Warning: Supabase credentials not configured")
        except Exception as e:
            print(f"Error initializing Supabase client: {e}")
            self.client = None
    
    def test_connection(self) -> dict:
        """Test Supabase connection"""
        if not self.client:
            return {
                "status": "error",
                "message": "Supabase client not initialized",
                "connected": False
            }
        
        try:
            # Simple query to test connection
            response = self.client.table("_test_connection").select("*").limit(1).execute()
            return {
                "status": "success",
                "message": "Supabase connection successful",
                "connected": True
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase connection failed: {str(e)}",
                "connected": False
            }
    
    def is_connected(self) -> bool:
        """Check if Supabase is connected"""
        return self.client is not None

# Global instance
supabase_service = SupabaseService()
