from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.api.routes import links, auth
from app.core.config import settings
from app.db.base import Base, engine


# TODO настроить нормальное логирование
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
* **Настройка времени действия ссылок** - задавайте свое время истечения ссылок

## Авторизация
Для управления ссылками необходимо сначала зарегистрироваться через `/auth/register`
"""


# TODO Кажется не очень хорошо инициализировать БД здесь и стоит вынести в другое место
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    try:
        logger.info("Проверка подключения к базе данных...")
        async with engine.begin() as conn:
            logger.info("Создание таблиц базы данных...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Таблицы успешно созданы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise e

    yield

    logger.info("Завершение работы приложения...")

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
    lifespan=lifespan,
)

# TODO настроить корректные значения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(links.router, tags=["links"])

@app.get("/", tags=["status"])
async def root():
    """
    Возвращает базовую информацию о состоянии API.
    """
    return {"message": """URL Cutter API работает. 
            Используйте `/docs` для доступа к интерактивной документации Swagger UI""",
            "status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 