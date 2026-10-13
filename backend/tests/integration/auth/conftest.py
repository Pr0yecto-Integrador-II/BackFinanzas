import uuid
from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings
from app.main import create_app
from app.modules.auth.api import deps
from app.shared.db import get_session
from tests.integration.conftest import TEST_URL
from tests.unit.auth.fakes import FakeLimiter, FakeMailer, FakeSeeder


class Env:
    def __init__(self, client: httpx.AsyncClient, limiter: FakeLimiter, mailer: FakeMailer) -> None:
        self.client = client
        self.limiter = limiter
        self.mailer = mailer


@pytest_asyncio.fixture
async def env(migrated_database: None) -> AsyncIterator[Env]:
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as c:
        await c.execute(text("TRUNCATE users CASCADE"))

    async def session() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    limiter, mailer = FakeLimiter(), FakeMailer()
    app = create_app()
    app.dependency_overrides.update(
        {
            get_session: session,
            deps.get_limiter: lambda: limiter,
            deps.get_mailer: lambda: mailer,
            get_settings: lambda: Settings(
                jwt_secret="test-secret-" + "x" * 32, cookie_secure=False
            ),
        }
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield Env(client, limiter, mailer)
    async with engine.begin() as c:  # no dejar datos a las demás pruebas
        await c.execute(text("TRUNCATE users CASCADE"))
    await engine.dispose()


async def register(env: Env, email: str = "ana@correo.com", password: str = "clave1234") -> dict:  # type: ignore[type-arg]
    res = await env.client.post(
        "/auth/register",
        json={"email": email, "password": password, "password_confirmation": password},
    )
    assert res.status_code == 201, res.text
    return res.json()  # type: ignore[no-any-return]


def new_id() -> str:
    return str(uuid.uuid4())


__all__ = ["Env", "FakeSeeder", "env", "new_id", "register"]
