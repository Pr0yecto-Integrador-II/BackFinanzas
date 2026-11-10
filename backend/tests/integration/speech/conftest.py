"""Cliente HTTP para `POST /speech/token` sin PostgreSQL ni Redis.

El JWT se sustituye por `FakeAccess` ("access:<uuid>"), el contador de Redis por
`FakeLimiter` y Azure por un proveedor falso o por `httpx.MockTransport`.
"""

import uuid
from collections.abc import AsyncIterator, Callable

import httpx
import pytest
import pytest_asyncio

from app.config import get_settings
from app.main import create_app
from app.modules.auth.api import deps as auth_deps
from app.modules.speech.api import deps as speech_deps
from app.modules.speech.application.ports import SpeechTokenProvider
from app.modules.speech.infrastructure.azure_token_provider import AzureSpeechTokenProvider
from tests.unit.auth.fakes import FakeAccess, FakeLimiter
from tests.unit.speech.fakes import FakeSpeechProvider

AZURE_KEY = "clave-azure-que-nunca-sale-del-servidor"


class SpeechApi:
    def __init__(self, client: httpx.AsyncClient, limiter: FakeLimiter) -> None:
        self.client = client
        self.limiter = limiter
        self.user = uuid.uuid4()

    def headers(self, user: uuid.UUID | None = None) -> dict[str, str]:
        return {"Authorization": f"Bearer access:{user or self.user}"}

    async def token(
        self, json: object | None = None, user: uuid.UUID | None = None
    ) -> httpx.Response:
        return await self.client.post("/speech/token", json=json, headers=self.headers(user))


ProviderFactory = Callable[[], SpeechTokenProvider]


def azure_with(handler: Callable[[httpx.Request], httpx.Response]) -> ProviderFactory:
    """Adaptador real de Azure con la red simulada."""
    return lambda: AzureSpeechTokenProvider(
        AZURE_KEY, "eastus", 5.0, transport=httpx.MockTransport(handler)
    )


@pytest.fixture
def provider_factory() -> ProviderFactory:
    """Por defecto, Azure responde un token válido. Cada prueba puede sobrescribirlo."""
    return lambda: FakeSpeechProvider()


@pytest_asyncio.fixture
async def api(
    monkeypatch: pytest.MonkeyPatch, provider_factory: ProviderFactory
) -> AsyncIterator[SpeechApi]:
    monkeypatch.setenv("JWT_SECRET", "speech-test-secret-" + "x" * 32)
    get_settings.cache_clear()
    limiter = FakeLimiter()
    app = create_app()
    app.dependency_overrides.update(
        {
            auth_deps.get_access_tokens: lambda: FakeAccess(),
            speech_deps.get_speech_counter: lambda: limiter,
            speech_deps.get_speech_provider: provider_factory,
        }
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield SpeechApi(client, limiter)
    get_settings.cache_clear()
