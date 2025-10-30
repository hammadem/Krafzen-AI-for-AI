"""Supabase client connection (singleton)."""
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

class SupabaseClient:
    _instance: Optional[Client] = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,  # Server-side full access
            )
        return getattr(self._instance, name)
    
    @classmethod
    def get_instance(cls) -> 'SupabaseClient':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

db = SupabaseClient.get_instance()
