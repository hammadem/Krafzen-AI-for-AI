"""
Supabase service for database operations
"""

from supabase import create_client, Client
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    """Supabase database service"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        # Check for SUPABASE_KEY (backward compatibility) or SUPABASE_ANON_KEY
        supabase_key = settings.SUPABASE_KEY or settings.SUPABASE_ANON_KEY
        
        if not settings.SUPABASE_URL or not supabase_key:
            logger.warning("Supabase credentials not configured. Some features may not work.")
            self.client = None
            return
        
        try:
            self.client = create_client(settings.SUPABASE_URL, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}")
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
