import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PROOFLINK API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database: SQLite default for seamless zero-config setup, PostgreSQL compatible
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./prooflink.db")
    
    # CORS: Allow frontend origins
    CORS_ORIGINS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Provider selection.  Mock providers are deliberately the default for
    # the local demo; production credentials must be supplied through env vars.
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "mock")
    TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER: str | None = os.getenv("TWILIO_FROM_NUMBER")
    KYC_PROVIDER: str = os.getenv("KYC_PROVIDER", "mock")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
