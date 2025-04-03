import valkey.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis():
    try:
        yield redis_client
    except Exception as e:
        raise e
    finally:
        pass
