import pytest

from app.modules.speech.domain.entities import SpeechToken
from app.modules.speech.domain.errors import SpeechRateLimitError, SpeechUnavailableError
from app.shared.errors import ServiceUnavailableError, TooManyRequestsError


@pytest.mark.parametrize("seconds", [1, 600])
def test_vigencia_valida(seconds: int) -> None:
    assert SpeechToken("t", "eastus", seconds).expires_in_seconds == seconds


@pytest.mark.parametrize("seconds", [0, -1, 601])
def test_vigencia_fuera_de_rango(seconds: int) -> None:
    with pytest.raises(ValueError):
        SpeechToken("t", "eastus", seconds)


@pytest.mark.parametrize(("token", "region"), [("", "eastus"), ("t", "")])
def test_token_y_region_obligatorios(token: str, region: str) -> None:
    with pytest.raises(ValueError):
        SpeechToken(token, region, 600)


def test_la_representacion_no_expone_el_token() -> None:
    assert "secreto" not in repr(SpeechToken("secreto", "eastus", 600))


def test_errores_se_traducen_a_503_y_429() -> None:
    assert isinstance(SpeechUnavailableError(), ServiceUnavailableError)
    assert isinstance(SpeechRateLimitError(), TooManyRequestsError)
