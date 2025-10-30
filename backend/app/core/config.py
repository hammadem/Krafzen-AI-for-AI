"""App configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str  # Client-side
    SUPABASE_SERVICE_ROLE_KEY: str  # Server-side ops
    
    # OpenAI (Weeks 3-4)
    OPENAI_API_KEY: str
    
    # App/Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Logging/Monitoring
    SENTRY_DSN: str | None = None
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
