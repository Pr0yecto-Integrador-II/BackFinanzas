from redis.asyncio import Redis


class RedisRateLimiter:
    def __init__(self, redis: Redis, prefix: str = "bf:") -> None:
        self._r = redis
        self._prefix = prefix

    async def incr(self, key: str, window_seconds: int) -> int:
        k = self._prefix + key
        async with self._r.pipeline(transaction=True) as pipe:
            pipe.incr(k)
            pipe.expire(k, window_seconds, nx=True)  # la ventana empieza en el primer fallo
            count, _ = await pipe.execute()
        return int(count)

    async def reset(self, key: str) -> None:
        await self._r.delete(self._prefix + key)

    async def set_flag(self, key: str, seconds: int) -> None:
        await self._r.set(self._prefix + key, "1", ex=seconds)

    async def has_flag(self, key: str) -> bool:
        return bool(await self._r.exists(self._prefix + key))
