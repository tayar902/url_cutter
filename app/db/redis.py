import valkey.asyncio as redis
from fastapi import Depends
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    logger.info(f"Redis подключен к {settings.REDIS_URL}")
except Exception as e:
    logger.error(f"Ошибка подключения к Redis: {e}")
    # Создаем заглушку для клиента Redis, чтобы приложение могло запуститься
    redis_client = None


async def get_redis():
    if redis_client is None:
        logger.warning("Redis клиент не инициализирован, возвращаем None")
        yield None

    try:
        yield redis_client
    except Exception as e:
        logger.error(f"Ошибка при использовании Redis: {e}")
        raise e
    finally:
        pass
