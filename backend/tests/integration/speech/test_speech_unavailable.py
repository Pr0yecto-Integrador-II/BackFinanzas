"""HU16 escenario 3: servicio de voz no configurado o caído → 503."""

import httpx
import pytest

from app.config import Settings
from app.modules.speech.api.deps import get_speech_provider
from tests.integration.speech.conftest import SpeechApi, azure_with

UNAVAILABLE = {
    "code": "SPEECH_SERVICE_UNAVAILABLE",
    "message": "El servicio de voz no está disponible en este momento",
}


def _timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("Azure tardó demasiado", request=request)


@pytest.mark.parametrize(
    "provider_factory",
    [
        azure_with(lambda _: httpx.Response(500)),
        azure_with(lambda _: httpx.Response(401)),
        azure_with(_timeout),
    ],
    ids=["azure-500", "clave-rechazada", "timeout"],
)
async def test_azure_falla_responde_503(api: SpeechApi) -> None:
    res = await api.token()
    assert res.status_code == 503
    assert res.json() == UNAVAILABLE


@pytest.mark.parametrize(
    "provider_factory",
    [lambda: get_speech_provider(Settings(jwt_secret="x" * 32))],
    ids=["sin-credenciales"],
)
async def test_sin_credenciales_configuradas_responde_503(api: SpeechApi) -> None:
    """La configuración real por defecto (sin AZURE_SPEECH_*) no rompe el arranque: da 503."""
    res = await api.token()
    assert res.status_code == 503
    assert res.json() == UNAVAILABLE


async def test_un_503_no_afecta_a_otros_endpoints(api: SpeechApi) -> None:
    assert (await api.client.get("/health")).json() == {"status": "ok"}
