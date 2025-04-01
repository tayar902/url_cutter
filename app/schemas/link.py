from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator


class LinkBase(BaseModel):
    """Базовая схема ссылки"""
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None


class LinkCreate(LinkBase):
    """Схема для создания ссылки"""
    pass


class LinkUpdate(BaseModel):
    """Схема для обновления ссылки"""
    original_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None


class LinkInDBBase(LinkBase):
    """Базовая схема ссылки в БД"""
    id: int
    short_code: str
    user_id: Optional[int] = None
    is_anonymous: bool = True
    clicks: int = 0
    created_at: datetime
    last_used_at: Optional[datetime] = None

    @field_validator("created_at", "last_used_at", "expires_at")
    def validate_datetime(cls, v):
        """Валидация даты и времени"""
        if v and not isinstance(v, datetime):
            raise ValueError("Значение должно быть датой и временем")
        return v


class Link(LinkInDBBase):
    """Схема ссылки для ответа"""
    short_url: Optional[str] = None


class LinkStats(BaseModel):
    """Схема статистики ссылки"""
    original_url: HttpUrl
    short_code: str
    short_url: str
    clicks: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class LinkSearch(BaseModel):
    """Схема для поиска ссылок"""
    id: int
    short_code: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None 