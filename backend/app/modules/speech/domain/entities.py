from dataclasses import dataclass

MAX_TOKEN_SECONDS = 600  # Azure AI Speech emite tokens de 10 minutos (HU16 regla 1)


@dataclass(frozen=True)
class SpeechToken:
    """Autorización temporal para usar Azure AI Speech desde el navegador (HU16)."""

    token: str
    region: str
    expires_in_seconds: int

    def __post_init__(self) -> None:
        if not self.token or not self.region:
            raise ValueError("El token y la región son obligatorios.")
        if not 0 < self.expires_in_seconds <= MAX_TOKEN_SECONDS:
            raise ValueError("La vigencia del token debe estar entre 1 y 600 segundos.")

    def __repr__(self) -> str:  # nunca imprimir el token en logs ni trazas
        return f"SpeechToken(region={self.region!r}, expires_in_seconds={self.expires_in_seconds})"
