"""
Configuration settings for KRAFZEN AI backend
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

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
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_PROJECT_ID: str = ""
    SUPABASE_KEY: str = ""  
    SUPABASE_ANON_KEY: str = ""  
    SUPABASE_SERVICE_ROLE_KEY: str = ""  
    SUPABASE_JWT_SECRET: str = ""
    # OpenAI API
    OPENAI_API_KEY: str = ""
    
    # GPT-4 Parser Configuration
    GPT_MODEL: str = "gpt-4-turbo-preview"
    GPT_MAX_TOKENS: int = 2000
    GPT_TEMPERATURE: float = 0.3
    
    # Hugging Face Configuration (for CADLLM model)
    HF_TOKEN: Optional[str] = None
    HF_MODEL_NAME: Optional[str] = None  # e.g., "username/cad-llm-krafzen"
    HF_ENDPOINT_URL: Optional[str] = None  # Optional: custom endpoint URL (e.g., Hugging Face Space)
    HF_TIMEOUT: int = 180  # Timeout in seconds for API calls
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: float = 25.0
    ALLOWED_AUDIO_FORMATS: str = "mp3,wav,m4a,ogg,flac,webm"
    
    @property
    def ALLOWED_AUDIO_FORMATS_LIST(self) -> List[str]:
        """Get ALLOWED_AUDIO_FORMATS as a list"""
        if not self.ALLOWED_AUDIO_FORMATS:
            return ["mp3", "wav", "m4a", "ogg", "flac", "webm"]
        return [fmt.strip().lower() for fmt in self.ALLOWED_AUDIO_FORMATS.split(',') if fmt.strip()]
    
    # App/Security
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Render
    PORT: int = 8000
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Render Configuration (optional)
    RENDER_SERVICE_ID_PRODUCTION: str = ""
    RENDER_SERVICE_ID_STAGING: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  

settings = Settings()
