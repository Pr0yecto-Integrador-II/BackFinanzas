"""Cliente HTTP para `POST /vision/analyze` sin PostgreSQL ni Redis.

El JWT se sustituye por `FakeAccess` ("access:<uuid>"), el contador de Redis por
`FakeLimiter` y Azure por un analizador falso o por `httpx.MockTransport`.
"""

import uuid
from collections.abc import AsyncIterator, Callable

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from app.config import get_settings
from app.main import create_app
from app.modules.auth.api import deps as auth_deps
from app.modules.vision.api import deps as vision_deps
from app.modules.vision.application.ports import ImageAnalyzer
from app.modules.vision.infrastructure.azure_image_analyzer import AzureImageAnalyzer
from tests.unit.auth.fakes import FakeAccess, FakeLimiter
from tests.unit.vision.fakes import FakeAnalyzer

AZURE_KEY = "clave-vision-que-nunca-sale-del-servidor"
MAX_BYTES = 2000


class VisionApi:
    def __init__(self, app: FastAPI, client: httpx.AsyncClient, limiter: FakeLimiter) -> None:
        self.app = app
        self.client = client
        self.limiter = limiter
        self.user = uuid.uuid4()

    def use_analyzer(self, factory: Callable[[], ImageAnalyzer]) -> None:
        """Cambia el analizador a mitad de la prueba."""
        self.app.dependency_overrides[vision_deps.get_vision_analyzer] = factory

    def headers(self, content_type: str, user: uuid.UUID | None = None) -> dict[str, str]:
        return {
            "Authorization": f"Bearer access:{user or self.user}",
            "Content-Type": content_type,
        }

    async def analyze(
        self,
        data: bytes,
        content_type: str = "image/jpeg",
        user: uuid.UUID | None = None,
    ) -> httpx.Response:
        return await self.client.post(
            "/vision/analyze", content=data, headers=self.headers(content_type, user)
        )


AnalyzerFactory = Callable[[], ImageAnalyzer]


def azure_with(handler: Callable[[httpx.Request], httpx.Response]) -> AnalyzerFactory:
    """Adaptador real de Azure con la red simulada."""
    return lambda: AzureImageAnalyzer(
        AZURE_KEY, "https://vision.example.com", 5.0, transport=httpx.MockTransport(handler)
    )


@pytest.fixture
def analyzer_factory() -> AnalyzerFactory:
    return lambda: FakeAnalyzer()


@pytest_asyncio.fixture
async def api(
    monkeypatch: pytest.MonkeyPatch, analyzer_factory: AnalyzerFactory
) -> AsyncIterator[VisionApi]:
    monkeypatch.setenv("JWT_SECRET", "vision-test-secret-" + "x" * 32)
    monkeypatch.setenv("VISION_MAX_IMAGE_BYTES", str(MAX_BYTES))
    monkeypatch.setenv("VISION_REQUESTS_PER_HOUR", "3")
    get_settings.cache_clear()
    limiter = FakeLimiter()
    app = create_app()
    app.dependency_overrides.update(
        {
            auth_deps.get_access_tokens: lambda: FakeAccess(),
            vision_deps.get_vision_counter: lambda: limiter,
            vision_deps.get_vision_analyzer: analyzer_factory,
        }
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield VisionApi(app, client, limiter)
    get_settings.cache_clear()
