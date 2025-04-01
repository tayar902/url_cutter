from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.session import init_db
# Импортируем все модели для правильной инициализации
from app.models.user import User
from app.models.link import Link

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    URL Cutter API - сервис для сокращения длинных URL.
    
    ## Возможности
    - Создание коротких ссылок без регистрации
    - Регистрация для доступа к дополнительным функциям
    - Управление своими ссылками
    - Просмотр статистики переходов
    - Установка срока действия ссылок
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    await init_db()

@app.get("/", tags=["status"])
async def root():
    """
    Возвращает базовую информацию о состоянии API.
    Используйте `/docs` для доступа к интерактивной документации Swagger UI.
    """
    return {"message": "URL Cutter API работает", "status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 