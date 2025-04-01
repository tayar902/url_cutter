from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.base import BaseModel
from app.core.config import settings


class Link(BaseModel):
    id = Column(Integer, primary_key=True, index=True)
    
    # Оригинальный URL
    original_url = Column(Text, nullable=False)
    
    # Короткий код для ссылки
    short_code = Column(String, unique=True, index=True, nullable=False)
    
    # Пользователь, создавший ссылку (может быть NULL для анонимных пользователей)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User", backref="links")
    
    # Счетчик переходов
    clicks = Column(Integer, default=0)
    
    # Время последнего использования
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Время истечения ссылки (устанавливается глобально)
    expires_at = Column(DateTime(timezone=True), nullable=True, 
                        default=lambda: datetime.now() + timedelta(days=settings.LINK_EXPIRATION_DAYS))
    
    # Флаг для проектов (дополнительная функциональность)
    project_id = Column(Integer, nullable=True)
    
    # Флаг активности
    is_active = Column(Boolean, default=True)
    
    # Флаг для анонимных ссылок
    is_anonymous = Column(Boolean, default=False) 