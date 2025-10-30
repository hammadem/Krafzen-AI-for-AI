"""
Configuration settings for KRAFZEN AI backend
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "KRAFZEN AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://staging.krafzen.com",
        "https://app.krafzen.com"
    ]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from environment variable"""
        if v is None or v == "":
            return [
                "http://localhost:3000",
                "https://*.vercel.app",
                "https://staging.krafzen.com",
                "https://app.krafzen.com"
            ]
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # OpenAI API
    OPENAI_API_KEY: str = ""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Render
    PORT: int = 8000
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

