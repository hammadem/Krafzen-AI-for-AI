import logging

from app.core.config import settings
from supabase import Client, create_client

logger = logging.getLogger(__name__)

class SupabaseClient:
    _client: Client | None = None

    def __getattr__(self, name):
        if self._client is None:
            # Only try to initialize if credentials are provided
            if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
                try:
                    self._client = create_client(
                        settings.SUPABASE_URL,
                        settings.SUPABASE_SERVICE_ROLE_KEY
                    )
                    logger.info("✅ Supabase service client initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Supabase init error: {e}")
                    self._client = None
            else:
                logger.warning("⚠️ Supabase credentials not configured, client not initialized")
                self._client = None

        if self._client is None:
            raise RuntimeError("Supabase client failed to initialize. Please check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your .env file")

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
