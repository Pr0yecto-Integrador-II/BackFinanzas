import asyncio
import uuid

from redis.asyncio import Redis

from app.modules.auth.infrastructure.rate_limiter import RedisRateLimiter


async def test_contador_con_ventana_y_reinicio() -> None:
    redis: Redis = Redis.from_url("redis://localhost:6380/0")
    limiter = RedisRateLimiter(redis, prefix=f"test:{uuid.uuid4()}:")
    try:
        assert [await limiter.incr("k", 60) for _ in range(3)] == [1, 2, 3]
        ttl = await redis.ttl(limiter._prefix + "k")
        assert 0 < ttl <= 60
        await limiter.reset("k")
        assert await limiter.incr("k", 60) == 1
    finally:
        await redis.delete(limiter._prefix + "k")
        await redis.aclose()


async def test_la_ventana_no_se_extiende_con_cada_fallo() -> None:
    redis: Redis = Redis.from_url("redis://localhost:6380/0")
    limiter = RedisRateLimiter(redis, prefix=f"test:{uuid.uuid4()}:")
    try:
        await limiter.incr("w", 2)
        await asyncio.sleep(1.1)
        await limiter.incr("w", 2)  # no debe renovar el TTL
        assert await redis.ttl(limiter._prefix + "w") <= 1
    finally:
        await redis.delete(limiter._prefix + "w")
        await redis.aclose()


async def test_bandera_de_bloqueo_vence_sola() -> None:
    redis: Redis = Redis.from_url("redis://localhost:6380/0")
    limiter = RedisRateLimiter(redis, prefix=f"test:{uuid.uuid4()}:")
    try:
        assert not await limiter.has_flag("lock")
        await limiter.set_flag("lock", 1)
        assert await limiter.has_flag("lock")
        await asyncio.sleep(1.2)
        assert not await limiter.has_flag("lock")
    finally:
        await redis.aclose()
