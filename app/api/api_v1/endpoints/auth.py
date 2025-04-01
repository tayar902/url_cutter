from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.deps import get_db, get_current_user
from app.crud import user as user_crud
from app.schemas.token import Token
from app.schemas.user import User, UserCreate

router = APIRouter()

@router.post("/register", response_model=User,
          summary="Регистрация пользователя",
          description="Создает нового пользователя и возвращает его данные")
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Регистрация нового пользователя"""
    user = await user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует",
        )
    
    user = await user_crud.create(db, obj_in=user_in)
    return user

@router.post("/login", response_model=Token,
          summary="Вход в систему",
          description="Аутентификация пользователя и получение токена доступа")
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """Вход в систему и получение токена"""
    user = await user_crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неактивный пользователь",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=User,
          summary="Информация о текущем пользователе",
          description="Возвращает данные текущего авторизованного пользователя")
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Получение информации о текущем пользователе"""
    return current_user 