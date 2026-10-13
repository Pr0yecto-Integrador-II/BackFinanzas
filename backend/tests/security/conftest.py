"""
Fixtures compartidos para pruebas de seguridad.
Reutilizan la infraestructura de integración.
"""

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings
from app.main import create_app
from app.modules.auth.api import deps
from app.shared.db import get_session
from tests.conftest import TEST_URL
from tests.unit.auth.fakes import FakeLimiter, FakeMailer


@pytest_asyncio.fixture
async def sec_client(migrated_database: None) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente HTTP limpio para pruebas de seguridad."""
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as c:
        await c.execute(text("TRUNCATE users CASCADE"))

    async def session() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    limiter = FakeLimiter()
    mailer = FakeMailer()
    app = create_app()
    app.dependency_overrides.update(
        {
            get_session: session,
            deps.get_limiter: lambda: limiter,
            deps.get_mailer: lambda: mailer,
            get_settings: lambda: Settings(
                jwt_secret="security-test-secret-" + "x" * 32, cookie_secure=False
            ),
        }
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    async with engine.begin() as c:
        await c.execute(text("TRUNCATE users CASCADE"))
    await engine.dispose()


async def _register_and_login(
    client: httpx.AsyncClient, email: str = "sec@correo.com"
) -> dict[str, Any]:
    res = await client.post(
        "/auth/register",
        json={"email": email, "password": "clave1234", "password_confirmation": "clave1234"},
    )
    assert res.status_code == 201, res.text
    return res.json()  # type: ignore[no-any-return]
