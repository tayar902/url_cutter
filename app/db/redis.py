from typing import AsyncGenerator
import valkey.asyncio as redis
from fastapi import Depends
from app.core.config import settings

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Получение клиента Redis"""
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.close()
