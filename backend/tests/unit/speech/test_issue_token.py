"""HU16 reglas 1, 3 y 4; HU19 (renovaciones durante una lectura larga)."""

import uuid

import pytest

from app.modules.speech.application.issue_token import (
    MAX_TOKENS_PER_WINDOW,
    WINDOW_SECONDS,
    IssueSpeechToken,
)
from app.modules.speech.domain.entities import SpeechToken
from app.modules.speech.domain.errors import SpeechRateLimitError, SpeechUnavailableError
from tests.unit.auth.fakes import FakeLimiter
from tests.unit.speech.fakes import FakeSpeechProvider


def _use_case(down: bool = False) -> tuple[IssueSpeechToken, FakeSpeechProvider, FakeLimiter]:
    provider, limiter = FakeSpeechProvider(down=down), FakeLimiter()
    return IssueSpeechToken(provider, limiter), provider, limiter


async def test_emite_token_temporal_con_region_y_vigencia() -> None:
    use_case, provider, _ = _use_case()
    token = await use_case.execute(uuid.uuid4())
    assert token == SpeechToken("tok-1", "eastus", 600)
    assert provider.calls == 1


async def test_la_cuota_es_de_30_por_hora_por_usuario() -> None:
    assert (MAX_TOKENS_PER_WINDOW, WINDOW_SECONDS) == (30, 3600)
    use_case, provider, limiter = _use_case()
    user = uuid.uuid4()
    for _ in range(30):
        await use_case.execute(user)
    with pytest.raises(SpeechRateLimitError) as exc:
        await use_case.execute(user)
    assert provider.calls == 30  # el intento 31 no llega a Azure
    assert exc.value.code == "SPEECH_RATE_LIMITED"
    assert limiter.counters == {f"speech:token:{user}": 31}


async def test_usuarios_distintos_tienen_cuotas_independientes() -> None:
    use_case, _, _ = _use_case()
    ana, luis = uuid.uuid4(), uuid.uuid4()
    for _ in range(30):
        await use_case.execute(ana)
    with pytest.raises(SpeechRateLimitError):
        await use_case.execute(ana)
    assert (await use_case.execute(luis)).region == "eastus"


async def test_proveedor_caido_responde_no_disponible() -> None:
    use_case, _, _ = _use_case(down=True)
    with pytest.raises(SpeechUnavailableError) as exc:
        await use_case.execute(uuid.uuid4())
    assert exc.value.code == "SPEECH_SERVICE_UNAVAILABLE"
    assert exc.value.message == "El servicio de voz no está disponible en este momento"


async def test_un_intento_fallido_tambien_consume_cuota() -> None:
    """Decisión de HU19: así un cliente que reintenta en bucle no satura Azure."""
    use_case, _, limiter = _use_case(down=True)
    user = uuid.uuid4()
    with pytest.raises(SpeechUnavailableError):
        await use_case.execute(user)
    assert limiter.counters[f"speech:token:{user}"] == 1


async def test_renovar_cada_540_segundos_durante_una_hora_no_agota_la_cuota() -> None:
    """HU19: una lectura de historial de 1 hora renueva el token unas 7 veces."""
    use_case, provider, _ = _use_case()
    user = uuid.uuid4()
    renewals = 3600 // 540 + 1
    tokens = [await use_case.execute(user) for _ in range(renewals)]
    assert len(tokens) == renewals < MAX_TOKENS_PER_WINDOW
    assert provider.calls == renewals
