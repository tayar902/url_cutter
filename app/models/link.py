from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.base import BaseModel
from app.core.config import settings


class Link(BaseModel):
    id = Column(Integer, primary_key=True, index=True,
                comment="Уникальный идентификатор ссылки")
    original_url = Column(Text, nullable=False,
                          comment="Оригинальный URL, который был сокращен")
    short_code = Column(String, unique=True, index=True,
                        nullable=False, comment="Короткий код для ссылки")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True,
                     comment="ID пользователя, создавшего ссылку")
    user = relationship("User", backref="links")
    clicks = Column(Integer, default=0,
                    comment="Количество переходов по ссылке")
    last_used_at = Column(DateTime(timezone=True), nullable=True,
                          comment="Дата и время последнего использования ссылки")
    expires_at = Column(DateTime(timezone=True), nullable=True, 
                        default=lambda: datetime.now() + timedelta(days=settings.LINK_EXPIRATION_DAYS),
                        comment="Дата и время истечения срока действия ссылки")
    project_id = Column(Integer, nullable=True,
                        comment="ID проекта, к которому относится ссылка")
    is_active = Column(Boolean, default=True, comment="Активна ли ссылка")
    is_anonymous = Column(Boolean, default=False,
                          comment="Создана ли ссылка анонимным пользователем")
