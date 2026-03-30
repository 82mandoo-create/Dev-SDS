from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    APP_NAME: str = "AssetGuard Enterprise"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str = "sqlite:///./assetguard.db"
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@assetguard.com"
    EMAIL_FROM_NAME: str = "AssetGuard System"
    
    OPENAI_API_KEY: str = ""
    
    AGENT_SECRET_KEY: str = "agent-secret-key-2024"
    
    FRONTEND_URL: str = "http://localhost:5173"
    
    ADMIN_EMAIL: str = "admin@company.com"
    ADMIN_PASSWORD: str = "Admin@123456"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
