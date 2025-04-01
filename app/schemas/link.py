from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class LinkBase(BaseModel):
    original_url: str = Field(
        ..., 
        description="Оригинальный URL для сокращения",
        example="https://www.example.com/very/long/url/that/needs/shortening"
    )
    
    @field_validator('original_url', mode='before')
    def validate_url(cls, v):
        # Простая валидация URL, можно расширить
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v


class LinkCreate(LinkBase):
    custom_alias: Optional[str] = Field(
        None, 
        description="Пользовательский алиас для короткой ссылки (опционально)", 
        example="mylink",
        min_length=3, 
        max_length=50
    )
    expires_at: Optional[datetime] = Field(
        None, 
        description="Дата и время истечения ссылки (в формате ISO 8601 с точностью до минуты)",
        example="2023-12-31T23:59:00Z"
    )


class LinkUpdate(BaseModel):
    original_url: Optional[str] = Field(
        None, 
        description="Новый оригинальный URL",
        example="https://www.new-example.com/updated/url"
    )
    
    @field_validator('original_url', mode='before')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v


class LinkInDBBase(LinkBase):
    id: int = Field(..., description="Уникальный идентификатор ссылки")
    short_code: str = Field(..., description="Короткий код для ссылки")
    clicks: int = Field(..., description="Количество переходов по ссылке")
    created_at: datetime = Field(..., description="Дата и время создания ссылки")
    last_used_at: Optional[datetime] = Field(None, description="Дата и время последнего использования")
    expires_at: Optional[datetime] = Field(None, description="Дата и время истечения ссылки")
    user_id: Optional[int] = Field(None, description="ID пользователя, создавшего ссылку")
    is_active: bool = Field(..., description="Активна ли ссылка")
    is_anonymous: bool = Field(..., description="Создана ли ссылка анонимным пользователем")
    
    class Config:
        orm_mode = True


class Link(LinkInDBBase):
    short_url: Optional[str] = Field(
        None, 
        description="Полный URL для короткой ссылки",
        example="http://localhost:8000/abc123"
    )


class LinkStats(BaseModel):
    original_url: str = Field(..., description="Оригинальный URL")
    short_code: str = Field(..., description="Короткий код ссылки")
    short_url: str = Field(..., description="Полный URL для короткой ссылки")
    clicks: int = Field(..., description="Количество переходов по ссылке")
    created_at: datetime = Field(..., description="Дата и время создания")
    last_used_at: Optional[datetime] = Field(None, description="Дата и время последнего использования")
    expires_at: Optional[datetime] = Field(None, description="Дата и время истечения")
    
    class Config:
        orm_mode = True


class LinkSearch(BaseModel):
    short_code: str = Field(..., description="Короткий код ссылки")
    original_url: str = Field(..., description="Оригинальный URL")
    
    class Config:
        orm_mode = True 