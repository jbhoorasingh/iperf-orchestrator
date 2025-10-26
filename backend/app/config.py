from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./iperf_orchestrator.db"
    
    # JWT Settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Admin User (for dev)
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # API Settings
    api_version: int = 1
    
    class Config:
        env_file = ".env"


settings = Settings()
