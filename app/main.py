from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.api.routes import links, auth
from app.core.config import settings
from app.db.base import Base, engine
# Импортируем все модели для правильной инициализации
from app.models.user import User
from app.models.link import Link

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

description = """
# URL Cutter API

Сервис для сокращения ссылок, аналогичный TinyURL или Bitly.

## Основные функции:
* **Создание коротких ссылок** - преобразование длинных URL в короткие
* **Перенаправление** - переход по коротким ссылкам на оригинальные URL
* **Статистика** - отслеживание количества переходов по ссылкам
* **Управление ссылками** - обновление, удаление, создание кастомных ссылок
* **Срок жизни** - настройка времени действия ссылок
* **Авторизация** - защита доступа к управлению ссылками

## Особенности
* **Создание ссылок без авторизации** - вы можете создавать короткие ссылки без регистрации
* **Управление ссылками с авторизацией** - регистрация дает доступ к дополнительным функциям
* **Настройка времени жизни** - задавайте свое время истечения ссылок

## Авторизация
Для управления ссылками необходимо сначала зарегистрироваться через `/auth/register`.
После регистрации вы автоматически получите токен доступа.

## Срок действия ссылок
Вы можете указать конкретное время истечения ссылки при создании через параметр `expires_at`.
Если время не указано, ссылке будет установлен срок жизни **{settings.LINK_EXPIRATION_DAYS} дней** с момента создания.
После истечения срока действия ссылка автоматически становится недоступной.
"""

app = FastAPI(
    title="URL Cutter API",
    description=description,
    version="0.1.0",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Операции аутентификации и регистрации пользователей",
        },
        {
            "name": "links",
            "description": "Операции с короткими ссылками: создание, редактирование, статистика и перенаправление",
        },
        {
            "name": "status",
            "description": "Проверка статуса API",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем таблицы при запуске приложения
@app.on_event("startup")
async def startup():
    logger.info("Запуск приложения...")
    try:
        # Проверяем подключение к базе данных
        logger.info("Проверка подключения к базе данных...")
        async with engine.begin() as conn:
            # Создаем таблицы, если они не существуют
            logger.info("Создание таблиц базы данных...")
            # Выводим все таблицы, которые будут созданы
            tables = Base.metadata.tables.keys()
            logger.info(f"Таблицы для создания: {', '.join(tables)}")
            
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Таблицы успешно созданы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise e

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(links.router, tags=["links"])

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