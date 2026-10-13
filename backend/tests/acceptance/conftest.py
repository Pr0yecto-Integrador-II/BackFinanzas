"""
Fixtures compartidos para pruebas de aceptación (BDD).
Reutilizan la infraestructura de tests/integration para no duplicar setup de BD.
"""

import asyncio
import importlib
import inspect
import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings
from app.main import create_app
from app.modules.auth.api import deps
from app.shared.db import get_session
from tests.conftest import TEST_URL
from tests.unit.auth.fakes import FakeLimiter, FakeMailer

_bdd_scenario_mod = importlib.import_module("pytest_bdd.scenario")
_orig_call_fixture_func = _bdd_scenario_mod.call_fixture_func


def _async_call_fixture_func(fixturefunc: Any, request: Any, kwargs: Any) -> Any:
    res = _orig_call_fixture_func(fixturefunc, request, kwargs)
    if inspect.iscoroutine(res):
        loop = request.getfixturevalue("event_loop")
        return loop.run_until_complete(res)
    return res


_bdd_scenario_mod.call_fixture_func = _async_call_fixture_func


class AcceptanceEnv:
    """Entorno completo para una prueba de aceptación: cliente HTTP + fakes."""

    def __init__(self, client: httpx.AsyncClient, mailer: FakeMailer, limiter: FakeLimiter) -> None:
        self.client = client
        self.mailer = mailer
        self.limiter = limiter
        # Estado compartido entre pasos de un mismo escenario
        self.last_response: httpx.Response | None = None
        self.access_token: str | None = None
        self.category_id: str | None = None
        self.category_id_2: str | None = None
        self.transaction_id: str | None = None
        self.reset_token: str | None = None
        self.pull_since: int = 0
        # Para escenarios multi-usuario
        self.tokens: dict[str, str] = {}

    def auth_headers(self, token: str | None = None) -> dict[str, str]:
        t = token or self.access_token
        return {"Authorization": f"Bearer {t}"} if t else {}

    async def register(
        self, email: str = "ana@correo.com", password: str = "clave1234"
    ) -> dict[str, Any]:
        res = await self.client.post(
            "/auth/register",
            json={"email": email, "password": password, "password_confirmation": password},
        )
        if res.status_code == 201:
            body = res.json()
            self.access_token = body["access_token"]
            self.tokens[email] = body["access_token"]
        self.last_response = res
        return res.json() if res.status_code == 201 else {}

    async def login(self, email: str, password: str) -> httpx.Response:
        res = await self.client.post("/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            self.access_token = res.json()["access_token"]
            self.tokens[email] = res.json()["access_token"]
        self.last_response = res
        return res

    async def pull(
        self, since: int = 0, limit: int = 500, token: str | None = None
    ) -> dict[str, Any]:
        res = await self.client.get(
            f"/sync/pull?since={since}&limit={limit}",
            headers=self.auth_headers(token),
        )
        self.last_response = res
        return res.json() if res.status_code == 200 else {}

    async def push(self, *changes: dict[str, Any], token: str | None = None) -> dict[str, Any]:
        res = await self.client.post(
            "/sync/push",
            json={"changes": list(changes)},
            headers=self.auth_headers(token),
        )
        self.last_response = res
        return res.json() if res.status_code == 200 else {}

    def new_id(self) -> str:
        return str(uuid.uuid4())

    def expense_tx(self, cat_id: str, **overrides: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": "expense",
            "amount_minor": 25_000_000,
            "category_id": cat_id,
            "occurred_on": "2026-10-01",
            "created_at": "2026-10-01T09:00:00Z",
            "tags": [],
        }
        data.update(overrides)
        tid = self.new_id()
        self.transaction_id = tid
        return {"entity": "transaction", "op": "upsert", "id": tid, "data": data}


@pytest.fixture
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def env(migrated_database: None, event_loop: asyncio.AbstractEventLoop) -> Iterator[AcceptanceEnv]:
    """Entorno de aceptación: BD limpia, cliente HTTP con fakes."""
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup() -> tuple[AcceptanceEnv, httpx.AsyncClient]:
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
                    jwt_secret="acceptance-secret-" + "x" * 32, cookie_secure=False
                ),
            }
        )
        transport = httpx.ASGITransport(app=app)
        client = httpx.AsyncClient(transport=transport, base_url="http://test")
        return AcceptanceEnv(client, mailer, limiter), client

    acc_env, client = event_loop.run_until_complete(_setup())
    yield acc_env

    async def _teardown() -> None:
        await client.aclose()
        async with engine.begin() as c:
            await c.execute(text("TRUNCATE users CASCADE"))
        await engine.dispose()

    event_loop.run_until_complete(_teardown())
