"""
Configuration settings for KRAFZEN AI backend
"""

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "KRAFZEN AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # CORS - Store as string to avoid JSON parsing issues with List[str]
    # Access via ALLOWED_ORIGINS_LIST property which converts to list
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://krafzen-ai-staging.vercel.app,https://*.vercel.app,https://staging.krafzen.com,https://app.krafzen.com"
    
    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list"""
        if not self.ALLOWED_ORIGINS:
            return [
                "http://localhost:3000",
                "https://krafzen-ai-staging.vercel.app",
                "https://*.vercel.app",
                "https://staging.krafzen.com",
                "https://app.krafzen.com"
            ]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]
    
    # OpenAI API
    OPENAI_API_KEY: str = ""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Render
    PORT: int = 8000
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # Render Configuration (optional)
    RENDER_SERVICE_ID_PRODUCTION: str = ""
    RENDER_SERVICE_ID_STAGING: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

settings = Settings()

