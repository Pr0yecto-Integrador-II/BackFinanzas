"""HU16 regla 2: la clave de Azure AI Speech nunca sale del servidor."""

import json
from pathlib import Path

from app.config import Settings
from app.modules.speech.api.schemas import SpeechTokenIn

BACKEND = Path(__file__).resolve().parents[2]
KEY = "clave-real-de-azure-que-no-debe-filtrarse"


def test_la_clave_no_aparece_al_imprimir_la_configuracion() -> None:
    settings = Settings(jwt_secret="x" * 32, azure_speech_key=KEY, azure_speech_region="eastus")
    assert KEY not in repr(settings)
    assert KEY not in str(settings.model_dump())
    assert settings.azure_speech_key is not None
    assert settings.azure_speech_key.get_secret_value() == KEY


def test_el_contrato_publico_no_expone_la_clave_ni_su_cabecera() -> None:
    spec = (BACKEND / "openapi.json").read_text(encoding="utf-8")
    assert "Ocp-Apim-Subscription-Key" not in spec
    assert "azure_speech_key" not in spec.lower()
    out = json.loads(spec)["components"]["schemas"]["SpeechTokenOut"]["properties"]
    assert set(out) == {"token", "region", "expires_in_seconds"}


def test_env_example_no_trae_una_clave_real() -> None:
    lines = (BACKEND / ".env.example").read_text(encoding="utf-8").splitlines()
    key_line = next(line for line in lines if line.startswith("AZURE_SPEECH_KEY="))
    assert key_line == "AZURE_SPEECH_KEY="


def test_el_cuerpo_no_admite_user_id_ni_claves() -> None:
    assert SpeechTokenIn.model_config.get("extra") == "forbid"
