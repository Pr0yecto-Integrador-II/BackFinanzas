"""HU18: el mismo token sirve para la síntesis y el contrato está documentado."""

import pytest

from tests.integration.speech.conftest import SpeechApi
from tests.unit.speech.fakes import FakeSpeechProvider


@pytest.mark.parametrize(
    "body", [{"voice": "es-CO-SalomeNeural"}, {"mode": "tts"}, {"locale": "es-CO"}]
)
async def test_no_acepta_voz_ni_modo_el_token_es_unico(
    api: SpeechApi, body: dict[str, str]
) -> None:
    """La voz la elige el cliente: el backend no recibe parámetros de síntesis."""
    assert (await api.token(json=body)).status_code == 422


async def test_un_mismo_token_para_dictado_y_lectura(api: SpeechApi) -> None:
    res = await api.token()
    assert res.status_code == 200
    assert res.json()["expires_in_seconds"] == 600
    assert res.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("provider_factory", [lambda: FakeSpeechProvider(down=True)])
async def test_fallo_del_servicio_de_sintesis(api: SpeechApi) -> None:
    """HU18 escenario 3: el cliente muestra "No se pudo reproducir el movimiento…"."""
    res = await api.token()
    assert res.status_code == 503
    assert res.json()["code"] == "SPEECH_SERVICE_UNAVAILABLE"


async def test_openapi_documenta_todas_las_respuestas(api: SpeechApi) -> None:
    spec = (await api.client.get("/openapi.json")).json()
    op = spec["paths"]["/speech/token"]["post"]
    assert {"200", "401", "422", "429", "503"} <= set(op["responses"])
    assert op["summary"] == "Emitir token temporal de voz"
    out = spec["components"]["schemas"]["SpeechTokenOut"]["properties"]
    assert set(out) == {"token", "region", "expires_in_seconds"}
