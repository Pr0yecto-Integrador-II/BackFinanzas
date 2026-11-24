"""HU20: la clave de Azure AI Vision y las imágenes nunca salen del servidor."""

import json
import logging
from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.main import create_app
from app.modules.auth.api import deps as auth_deps
from app.modules.vision.api import deps as vision_deps
from tests.unit.auth.fakes import FakeAccess, FakeLimiter
from tests.unit.vision.fakes import JPEG, FakeAnalyzer

BACKEND = Path(__file__).resolve().parents[2]
KEY = "clave-real-de-vision-que-no-debe-filtrarse"


def test_la_clave_no_aparece_al_imprimir_la_configuracion() -> None:
    settings = Settings(
        jwt_secret="x" * 32, azure_vision_key=KEY, azure_vision_endpoint="https://v.example.com"
    )
    assert KEY not in repr(settings)
    assert KEY not in str(settings.model_dump())
    assert settings.azure_vision_key is not None
    assert settings.azure_vision_key.get_secret_value() == KEY


def test_el_contrato_publico_no_expone_la_clave_ni_su_cabecera() -> None:
    spec = json.loads((BACKEND / "openapi.json").read_text(encoding="utf-8"))
    text = json.dumps(spec)
    assert "Ocp-Apim-Subscription-Key" not in text
    assert "azure_vision_key" not in text.lower()
    assert set(spec["components"]["schemas"]["ImageAnalysisOut"]["properties"]) == {
        "ocr_lines",
        "tags",
        "caption",
    }


def test_env_example_no_trae_una_clave_real() -> None:
    lines = (BACKEND / ".env.example").read_text(encoding="utf-8").splitlines()
    assert (
        next(line for line in lines if line.startswith("AZURE_VISION_KEY=")) == "AZURE_VISION_KEY="
    )


def test_el_resultado_no_imprime_el_texto_leido() -> None:
    from app.modules.vision.domain.entities import ImageAnalysis

    result = ImageAnalysis(ocr_lines=("CUENTA 123-456",), tags=(), caption=None)
    assert "123-456" not in repr(result)


async def test_los_logs_de_una_peticion_no_traen_imagen_ni_texto_leido(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("JWT_SECRET", "vision-security-" + "x" * 32)
    from app.config import get_settings

    get_settings.cache_clear()
    caplog.set_level(logging.DEBUG)
    app = create_app()
    app.dependency_overrides.update(
        {
            auth_deps.get_access_tokens: lambda: FakeAccess(),
            vision_deps.get_vision_counter: lambda: FakeLimiter(),
            vision_deps.get_vision_analyzer: lambda: FakeAnalyzer(),
        }
    )
    image = JPEG + b"MARCA-UNICA-DE-LA-IMAGEN"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.post(
            "/vision/analyze",
            content=image,
            headers={
                "Authorization": "Bearer access:00000000-0000-0000-0000-000000000001",
                "Content-Type": "image/jpeg",
            },
        )
    assert res.status_code == 200
    assert "MARCA-UNICA" not in caplog.text
    assert "45.900" not in caplog.text
    get_settings.cache_clear()
