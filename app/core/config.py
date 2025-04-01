from pydantic_settings import BaseSettings
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "URL Cutter"
    API_V1_STR: str = ""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "test_secret_key")
    
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8))
    
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "url_cutter"
    POSTGRES_PORT: int = 5433
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Link settings
    LINK_EXPIRATION_DAYS: int = 180  # Default link expiration (if not specified)
    SHORT_CODE_LENGTH: int = 6  # Default short code length
    
    # Base URL for short links
    BASE_URL: str = "http://localhost:8000"
    
    @property
    def DATABASE_URL(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        case_sensitive = True

settings = Settings() 