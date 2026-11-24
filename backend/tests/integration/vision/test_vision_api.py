"""HU20 sobre la API: 200, 401, 413, 415, 429 y 503."""

import uuid

import httpx
import pytest

from tests.integration.vision.conftest import (
    AZURE_KEY,
    MAX_BYTES,
    AnalyzerFactory,
    VisionApi,
    azure_with,
)
from tests.unit.vision.fakes import JPEG, PNG, FakeAnalyzer

AZURE_BODY = {
    "captionResult": {"text": "a plate of pizza", "confidence": 0.8},
    "readResult": {"blocks": [{"lines": [{"text": "TOTAL 45.900"}]}]},
    "tagsResult": {"values": [{"name": "food", "confidence": 0.9}]},
}


@pytest.fixture
def analyzer_factory() -> AnalyzerFactory:
    return azure_with(lambda request: httpx.Response(200, json=AZURE_BODY))


async def test_analisis_exitoso(api: VisionApi) -> None:
    res = await api.analyze(JPEG)
    assert res.status_code == 200
    assert res.json() == {
        "ocr_lines": ["TOTAL 45.900"],
        "tags": [{"name": "food", "confidence": 0.9}],
        "caption": "a plate of pizza",
    }
    assert res.headers["Cache-Control"] == "no-store"
    assert AZURE_KEY not in res.text


async def test_acepta_png_y_parametros_en_el_content_type(api: VisionApi) -> None:
    assert (await api.analyze(PNG, "image/png")).status_code == 200
    assert (await api.analyze(JPEG, "image/jpeg; charset=binary")).status_code == 200


async def test_sin_sesion_responde_401(api: VisionApi) -> None:
    res = await api.client.post(
        "/vision/analyze", content=JPEG, headers={"Content-Type": "image/jpeg"}
    )
    assert res.status_code == 401


async def test_imagen_demasiado_grande_responde_413(api: VisionApi) -> None:
    res = await api.analyze(JPEG + b"\x00" * MAX_BYTES)
    assert res.status_code == 413
    assert res.json() == {"code": "IMAGE_TOO_LARGE", "message": "La imagen es demasiado grande"}


async def test_cuerpo_en_trozos_sin_content_length_tambien_se_limita(api: VisionApi) -> None:
    async def chunks():  # type: ignore[no-untyped-def]
        for _ in range(5):
            yield JPEG + b"\x00" * (MAX_BYTES // 2)

    res = await api.client.post(
        "/vision/analyze", content=chunks(), headers=api.headers("image/jpeg")
    )
    assert res.status_code == 413


@pytest.mark.parametrize(
    ("data", "content_type", "code"),
    [
        (b"%PDF-1.7 hola", "image/jpeg", "UNSUPPORTED_IMAGE"),
        (JPEG, "application/json", "UNSUPPORTED_IMAGE"),
        (b"", "image/jpeg", "EMPTY_IMAGE"),
    ],
)
async def test_archivo_no_admitido_responde_415(
    api: VisionApi, data: bytes, content_type: str, code: str
) -> None:
    res = await api.analyze(data, content_type)
    assert res.status_code == 415
    assert res.json()["code"] == code


async def test_limite_por_hora_responde_429(api: VisionApi) -> None:
    for _ in range(3):
        assert (await api.analyze(JPEG)).status_code == 200
    res = await api.analyze(JPEG)
    assert res.status_code == 429
    assert res.json() == {
        "code": "VISION_RATE_LIMITED",
        "message": "Has alcanzado el límite temporal de análisis de imágenes. Intenta más tarde",
    }
    assert (await api.analyze(JPEG, user=uuid.uuid4())).status_code == 200  # cuota por usuario


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_azure_caido_responde_503_y_consume_cuota(api: VisionApi, status: int) -> None:
    api.use_analyzer(azure_with(lambda request: httpx.Response(status)))
    res = await api.analyze(JPEG)
    assert res.status_code == 503
    assert res.json() == {
        "code": "VISION_SERVICE_UNAVAILABLE",
        "message": "El análisis de imágenes no está disponible en este momento",
    }
    assert api.limiter.counters[f"vision:analyze:{api.user}"] == 1
    assert AZURE_KEY not in res.text


async def test_el_analizador_no_recibe_imagenes_rechazadas(api: VisionApi) -> None:
    fake = FakeAnalyzer()
    api.use_analyzer(lambda: fake)
    await api.analyze(b"basura", "image/jpeg")
    await api.analyze(JPEG + b"\x00" * MAX_BYTES)
    assert fake.calls == []
