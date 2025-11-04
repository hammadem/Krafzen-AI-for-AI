from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    _client: Optional[Client] = None

    def __getattr__(self, name):
        if self._client is None:
            try:
                self._client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                logger.info("✅ Supabase service client initialized")
            except Exception as e:
                logger.error(f"❌ Supabase init error: {e}")
                self._client = None

        if self._client is None:
            raise RuntimeError("Supabase client failed to initialize")

        return getattr(self._client, name)

    @classmethod
    def get_instance(cls) -> 'SupabaseClient':
        return cls()

# Global instance
db = SupabaseClient.get_instance()


def create_user_client(token: str) -> Client:
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
        options={
            "global": {
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        },
    )
