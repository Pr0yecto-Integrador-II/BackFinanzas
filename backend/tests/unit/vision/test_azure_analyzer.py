"""Adaptador de Azure AI Vision con la red simulada (httpx.MockTransport)."""

import logging

import httpx
import pytest

from app.modules.vision.domain.errors import VisionUnavailableError
from app.modules.vision.infrastructure.azure_image_analyzer import AzureImageAnalyzer
from tests.unit.vision.fakes import JPEG

KEY = "clave-super-secreta-de-vision"
ENDPOINT = "https://mi-recurso.cognitiveservices.azure.com/"
OK_BODY = {
    "captionResult": {"text": "a plate of pizza", "confidence": 0.8},
    "readResult": {
        "blocks": [{"lines": [{"text": "ÉXITO"}, {"text": "  "}, {"text": "TOTAL 45.900"}]}]
    },
    "tagsResult": {
        "values": [{"name": "Food", "confidence": 0.93}, {"name": "pizza", "confidence": 0.8}]
    },
}


def _analyzer(
    handler: object, key: str | None = KEY, endpoint: str | None = ENDPOINT
) -> AzureImageAnalyzer:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return AzureImageAnalyzer(key, endpoint, 5.0, transport=transport)


async def test_envia_la_imagen_cruda_con_la_clave_y_traduce_la_respuesta() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=OK_BODY)

    result = await _analyzer(handler).analyze(JPEG, "image/jpeg")
    req = seen[0]
    assert req.method == "POST"
    assert req.url.path == "/computervision/imageanalysis:analyze"
    assert req.url.params["features"] == "read,tags"  # caption no existe en todas las regiones
    assert req.url.params["api-version"] == "2023-10-01"
    assert req.headers["Ocp-Apim-Subscription-Key"] == KEY
    assert req.content == JPEG
    assert result.ocr_lines == ("ÉXITO", "TOTAL 45.900")  # sin líneas en blanco
    assert [(t.name, t.confidence) for t in result.tags] == [("food", 0.93), ("pizza", 0.8)]
    assert result.caption == "a plate of pizza"


async def test_respuesta_sin_secciones_da_un_analisis_vacio() -> None:
    result = await _analyzer(lambda r: httpx.Response(200, json={})).analyze(JPEG, "image/jpeg")
    assert result.ocr_lines == () and result.tags == () and result.caption is None


@pytest.mark.parametrize(
    ("key", "endpoint"),
    [(None, ENDPOINT), (KEY, None), ("", ENDPOINT), (KEY, "http://inseguro.example.com")],
)
async def test_sin_credenciales_o_sin_https_no_llama_a_azure(
    key: str | None, endpoint: str | None
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=OK_BODY)

    with pytest.raises(VisionUnavailableError):
        await _analyzer(handler, key, endpoint).analyze(JPEG, "image/jpeg")
    assert calls == []


@pytest.mark.parametrize("status", [400, 401, 429, 500])
async def test_estado_distinto_de_200_es_no_disponible(status: int) -> None:
    with pytest.raises(VisionUnavailableError):
        await _analyzer(lambda r: httpx.Response(status)).analyze(JPEG, "image/jpeg")


async def test_timeout_y_error_de_red_son_no_disponibles() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("lento", request=request)

    with pytest.raises(VisionUnavailableError):
        await _analyzer(boom).analyze(JPEG, "image/jpeg")


@pytest.mark.parametrize(
    "body", [{"tagsResult": {"values": [{"name": "x"}]}}, ["no", "es", "dict"]]
)
async def test_respuesta_con_forma_inesperada_es_no_disponible(body: object) -> None:
    with pytest.raises(VisionUnavailableError):
        await _analyzer(lambda r: httpx.Response(200, json=body)).analyze(JPEG, "image/jpeg")


async def test_los_logs_no_contienen_clave_ni_texto_leido(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json=OK_BODY)

    with pytest.raises(VisionUnavailableError):
        await _analyzer(handler).analyze(JPEG, "image/jpeg")
    assert KEY not in caplog.text
    assert "45.900" not in caplog.text and "ÉXITO" not in caplog.text


@pytest.mark.parametrize(
    ("configured", "sent"),
    [
        ("read,tags,caption", "read,tags,caption"),
        (" caption , read ", "caption,read"),
        ("read,read,tags", "read,tags"),
        ("denseCaptions,people", "read,tags"),  # desconocidas: vuelve al valor por defecto
        ("", "read,tags"),
    ],
)
async def test_las_caracteristicas_son_configurables_pero_solo_las_conocidas(
    configured: str, sent: str
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=OK_BODY)

    analyzer = AzureImageAnalyzer(
        KEY, ENDPOINT, 5.0, transport=httpx.MockTransport(handler), features=configured
    )
    await analyzer.analyze(JPEG, "image/jpeg")
    assert seen[0].url.params["features"] == sent
