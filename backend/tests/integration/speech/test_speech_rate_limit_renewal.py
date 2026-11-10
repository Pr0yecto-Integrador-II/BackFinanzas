"""HU19: la cuota de tokens de voz con Redis real (docker compose, puerto 6380)."""

import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from app.modules.auth.infrastructure.rate_limiter import RedisRateLimiter
from app.modules.speech.application.issue_token import IssueSpeechToken
from app.modules.speech.domain.errors import SpeechRateLimitError
from tests.unit.speech.fakes import FakeSpeechProvider


@pytest_asyncio.fixture
async def limiter() -> AsyncIterator[RedisRateLimiter]:
    redis: Redis = Redis.from_url("redis://localhost:6380/0")
    limiter = RedisRateLimiter(redis, prefix=f"test:{uuid.uuid4()}:")
    try:
        yield limiter
    finally:
        keys = [k async for k in redis.scan_iter(match=limiter._prefix + "*")]
        if keys:
            await redis.delete(*keys)
        await redis.aclose()


async def test_peticiones_concurrentes_cuentan_de_forma_atomica(
    limiter: RedisRateLimiter,
) -> None:
    use_case = IssueSpeechToken(FakeSpeechProvider(), limiter)
    user = uuid.uuid4()
    await asyncio.gather(*(use_case.execute(user) for _ in range(5)))
    assert await limiter.incr(f"speech:token:{user}", 3600) == 6  # 5 previas + esta


async def test_rafaga_concurrente_solo_deja_pasar_30(limiter: RedisRateLimiter) -> None:
    use_case = IssueSpeechToken(FakeSpeechProvider(), limiter)
    user = uuid.uuid4()
    results = await asyncio.gather(
        *(use_case.execute(user) for _ in range(35)), return_exceptions=True
    )
    rejected = [r for r in results if isinstance(r, SpeechRateLimitError)]
    assert len(results) - len(rejected) == 30
    assert len(rejected) == 5


async def test_la_ventana_dura_una_hora_y_luego_se_reinicia(limiter: RedisRateLimiter) -> None:
    provider = FakeSpeechProvider()
    use_case = IssueSpeechToken(provider, limiter)
    user = uuid.uuid4()
    key = limiter._prefix + f"speech:token:{user}"
    for _ in range(30):
        await use_case.execute(user)
    with pytest.raises(SpeechRateLimitError):
        await use_case.execute(user)
    assert 3590 < await limiter._r.ttl(key) <= 3600
    await limiter._r.expire(key, 1)  # simula que pasó la hora
    await asyncio.sleep(1.2)
    assert (await use_case.execute(user)).region == "eastus"
