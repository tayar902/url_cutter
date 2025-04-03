from pydantic_settings import BaseSettings
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "URL Cutter"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "test_secret_key")
    
    # дефолтно 8 дней
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8))
    
    ALGORITHM: str = "HS256"
    
    # Подключение к postgres
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "url_cutter")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("DATABASE_URL")
    
    # Подключение к reidis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Параметры для ссылок
    LINK_EXPIRATION_DAYS: int = 180
    SHORT_CODE_LENGTH: int = 6
    
    # Основной URL
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    @property
    def DATABASE_URL(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        case_sensitive = True


settings = Settings()
