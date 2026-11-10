"""HU16 (autorización segura) y HU17 (el token sirve para el dictado) sobre la API."""

import httpx
import pytest

from tests.integration.speech.conftest import AZURE_KEY, ProviderFactory, SpeechApi, azure_with


def _azure_ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text="eyJ-token-temporal")


@pytest.fixture
def provider_factory() -> ProviderFactory:
    return azure_with(_azure_ok)


async def test_obtencion_exitosa_de_token_temporal(api: SpeechApi) -> None:
    """HU16 escenario 1: token, región "eastus" y 600 s, sin la clave de suscripción."""
    res = await api.token()
    assert res.status_code == 200
    assert res.json() == {
        "token": "eyJ-token-temporal",
        "region": "eastus",
        "expires_in_seconds": 600,
    }
    assert AZURE_KEY not in res.text
    assert res.headers["Cache-Control"] == "no-store"


async def test_acepta_cuerpo_vacio(api: SpeechApi) -> None:
    assert (await api.token(json={})).status_code == 200


async def test_sin_sesion_responde_401(api: SpeechApi) -> None:
    res = await api.client.post("/speech/token")
    assert res.status_code == 401


async def test_token_de_sesion_invalido_responde_401(api: SpeechApi) -> None:
    res = await api.client.post("/speech/token", headers={"Authorization": "Bearer basura"})
    assert res.status_code == 401


@pytest.mark.parametrize(
    "body", [{"user_id": "00000000-0000-0000-0000-000000000000"}, {"key": "x"}]
)
async def test_campos_extra_se_rechazan_con_422(api: SpeechApi, body: dict[str, str]) -> None:
    """`extra="forbid"`: ni el `user_id` ni una clave pueden llegar por el cuerpo."""
    assert (await api.token(json=body)).status_code == 422


async def test_limite_de_solicitudes_excedido(api: SpeechApi) -> None:
    """HU16 escenario 2: la solicitud 31 de la hora responde 429."""
    for _ in range(30):
        assert (await api.token()).status_code == 200
    res = await api.token()
    assert res.status_code == 429
    assert res.json() == {
        "code": "SPEECH_RATE_LIMITED",
        "message": "Has alcanzado el límite temporal del servicio de voz. Intenta más tarde",
    }
    assert api.limiter.counters == {f"speech:token:{api.user}": 31}


async def test_la_cuota_usa_el_user_id_del_token(api: SpeechApi) -> None:
    other = api.user.__class__(int=api.user.int ^ 1)
    await api.token(user=other)
    assert set(api.limiter.counters) == {f"speech:token:{other}"}


async def test_el_token_sirve_para_el_dictado_sin_parametros_adicionales(api: SpeechApi) -> None:
    """HU17: el cliente usa `SpeechConfig.fromAuthorizationToken(token, region)`."""
    body = (await api.token()).json()
    assert set(body) == {"token", "region", "expires_in_seconds"}
    assert body["token"] and body["region"]
