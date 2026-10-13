"""Piezas compartidas de la aplicación, inyectadas con `Depends`.

Los tests las sustituyen con `app.dependency_overrides`.
"""

from functools import lru_cache

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from redis.asyncio import Redis

from app.config import Settings, get_settings
from app.shared.clock import Clock, SystemClock


def get_clock() -> Clock:
    return SystemClock()


@lru_cache
def _redis(url: str) -> Redis:
    client: Redis = Redis.from_url(url)
    return client


def get_redis() -> Redis:
    return _redis(get_settings().redis_url)


_arq_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    return _arq_pool


__all__ = ["Settings", "get_arq_pool", "get_clock", "get_redis", "get_settings"]
