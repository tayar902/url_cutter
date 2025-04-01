from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.crud import user as user_crud

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED,
            summary="Регистрация нового пользователя",
            description="Создает нового пользователя и возвращает токен доступа")
async def register(
    user_in: UserCreate = Body(..., example={
        "email": "user@example.com",
        "username": "testuser",
        "password": "strongpassword123"
    }),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Регистрация нового пользователя в системе.
    
    - **email**: уникальный email пользователя (обязательно)
    - **username**: уникальное имя пользователя (обязательно)
    - **password**: пароль пользователя (обязательно)
    
    При успешной регистрации сразу возвращает токен доступа, 
    который можно использовать для авторизованных запросов.
    """
    # Проверяем, существует ли пользователь с таким email
    user = await user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует",
        )
        
    # Проверяем, существует ли пользователь с таким username
    user = await user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем уже существует",
        )
        
    # Создаем пользователя
    user = await user_crud.create(db, obj_in=user_in)
    
    # Создаем и возвращаем токен доступа
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token,
            summary="Авторизация пользователя",
            description="Получение JWT токена для аутентификации в API")
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Авторизация пользователя и получение токена доступа.
    
    - **username**: email или имя пользователя
    - **password**: пароль пользователя
    
    При успешной авторизации возвращает JWT токен, который необходимо 
    использовать в заголовке Authorization для защищенных эндпоинтов.
    
    Пример использования: 
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
    """
    user = await user_crud.authenticate(
        db=db, email_or_username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный email/имя пользователя или пароль",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неактивный пользователь",
        )
        
    # Создаем токен доступа
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    } 