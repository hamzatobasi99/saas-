from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Smart AI WhatsApp Agent"

    # Database & Security
    DATABASE_URL: str
    SECRET_KEY: str  # Used for encrypting WhatsApp Tokens
    SUPABASE_JWT_SECRET: Optional[str] = None # Added for Supabase Auth verification
    
    # Qdrant Vector Store
    QDRANT_URL: str = ":memory:"
    QDRANT_API_KEY: Optional[str] = None

    # AI Configuration
    AI_PROVIDER: str = "openai"  # Pluggable architecture
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    AI_REQUEST_TIMEOUT: int = 30
    
    # Meta / WhatsApp
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()