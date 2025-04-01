from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    email: Optional[EmailStr] = Field(
        None, 
        description="Email пользователя",
        example="user@example.com"
    )
    username: Optional[str] = Field(
        None, 
        description="Имя пользователя",
        example="johndoe"
    )
    is_active: Optional[bool] = Field(
        True, 
        description="Флаг активности пользователя"
    )


class UserCreate(UserBase):
    email: EmailStr = Field(
        ..., 
        description="Email пользователя (обязательно)",
        example="user@example.com"
    )
    username: str = Field(
        ..., 
        description="Имя пользователя (обязательно)",
        example="johndoe",
        min_length=3,
        max_length=50
    )
    password: str = Field(
        ..., 
        description="Пароль пользователя (обязательно)",
        example="password123",
        min_length=6
    )


class UserUpdate(UserBase):
    password: Optional[str] = Field(
        None, 
        description="Новый пароль пользователя (опционально)",
        example="newpassword123",
        min_length=6
    )


class UserInDBBase(UserBase):
    id: Optional[int] = Field(
        None, 
        description="Уникальный идентификатор пользователя"
    )

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str = Field(
        ..., 
        description="Хешированный пароль пользователя (для внутреннего использования)"
    ) 