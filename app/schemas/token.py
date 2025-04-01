from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Схема токена"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Схема данных токена"""
    sub: Optional[int] = None 