from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserInDBBase(UserBase):
    """Базовая схема пользователя в БД"""
    id: int


class User(UserInDBBase):
    """Схема пользователя для ответа"""
    pass


class UserInDB(UserInDBBase):
    """Схема пользователя в БД"""
    hashed_password: str 