"""Adaptador del STS de Azure AI Speech con la red simulada (httpx.MockTransport)."""

import logging

import httpx
import pytest

from app.modules.speech.domain.errors import SpeechUnavailableError
from app.modules.speech.infrastructure.azure_token_provider import AzureSpeechTokenProvider

KEY = "clave-super-secreta-de-azure"


def _provider(handler: object, key: str | None = KEY, region: str | None = "eastus") -> object:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return AzureSpeechTokenProvider(key, region, 5.0, transport=transport)


async def test_pide_el_token_al_sts_de_la_region_con_la_clave() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, text="eyJ-token-temporal")

    token = await _provider(handler).issue()  # type: ignore[attr-defined]
    assert (token.token, token.region, token.expires_in_seconds) == (
        "eyJ-token-temporal",
        "eastus",
        600,
    )
    req = seen[0]
    assert req.method == "POST"
    assert str(req.url) == "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    assert req.headers["Ocp-Apim-Subscription-Key"] == KEY


@pytest.mark.parametrize(("key", "region"), [(None, "eastus"), (KEY, None), ("", "eastus")])
async def test_sin_credenciales_no_llama_a_azure(key: str | None, region: str | None) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, text="x")

    with pytest.raises(SpeechUnavailableError):
        await _provider(handler, key, region).issue()  # type: ignore[attr-defined]
    assert calls == []


@pytest.mark.parametrize(
    "response", [httpx.Response(401), httpx.Response(500), httpx.Response(200, text="  ")]
)
async def test_respuesta_invalida_de_azure(response: httpx.Response) -> None:
    with pytest.raises(SpeechUnavailableError):
        await _provider(lambda _: response).issue()  # type: ignore[attr-defined]


@pytest.mark.parametrize("error", [httpx.ConnectTimeout("timeout"), httpx.ConnectError("sin red")])
async def test_timeout_o_red_caida(error: Exception) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    with pytest.raises(SpeechUnavailableError):
        await _provider(handler).issue()  # type: ignore[attr-defined]


async def test_los_logs_no_contienen_la_clave_ni_el_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"fallo con {request.headers['Ocp-Apim-Subscription-Key']}")

    with pytest.raises(SpeechUnavailableError):
        await _provider(fail).issue()  # type: ignore[attr-defined]
    await _provider(lambda _: httpx.Response(200, text="tok-visible")).issue()  # type: ignore[attr-defined]
    assert KEY not in caplog.text
    assert "tok-visible" not in caplog.text
