from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func
from sqlalchemy import Column, DateTime, Integer
from typing import Any
from datetime import datetime

from app.core.config import settings
from app.db.base_class import Base
from app.models.link import Link
from app.models.user import User

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Base:
    """Базовый класс для всех моделей"""
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @declared_attr
    def __tablename__(cls) -> str:
        """Генерирует имя таблицы из имени класса"""
        return cls.__name__.lower()

    def dict(self) -> dict[str, Any]:
        """Преобразует модель в словарь"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 