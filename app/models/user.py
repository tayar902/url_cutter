from sqlalchemy import Boolean, Column, Integer, String
from app.db.base import BaseModel


class User(BaseModel):
    id = Column(Integer, primary_key=True, index=True,
                comment="Уникальный идентификатор пользователя")
    email = Column(String, unique=True, index=True,
                   nullable=False, comment="Email пользователя")
    username = Column(String, unique=True, index=True,
                      nullable=False, comment="Имя пользователя")
    hashed_password = Column(String, nullable=False,
                             comment="Хешированный пароль пользователя")
    is_active = Column(Boolean, default=True,
                       comment="Активен ли пользователь")
    is_superuser = Column(Boolean, default=False,
                          comment="Является ли пользователь администратором")
