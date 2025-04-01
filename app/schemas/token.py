from pydantic import BaseModel, Field
from typing import Optional


class Token(BaseModel):
    access_token: str = Field(
        ..., 
        description="JWT токен доступа",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MTY4NjU0MjIsInN1YiI6IjEifQ.example"
    )
    token_type: str = Field(
        ..., 
        description="Тип токена",
        example="bearer"
    )


class TokenPayload(BaseModel):
    sub: Optional[int] = Field(
        None, 
        description="Идентификатор пользователя (subject)",
        example=1
    ) 