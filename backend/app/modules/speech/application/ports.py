from typing import Protocol

from app.modules.speech.domain.entities import SpeechToken


class SpeechTokenProvider(Protocol):
    async def issue(self) -> SpeechToken:
        """Pide un token temporal al proveedor. Lanza SpeechUnavailableError si falla."""
        ...


class RequestCounter(Protocol):
    async def incr(self, key: str, window_seconds: int) -> int:
        """Suma 1 al contador de la ventana (de forma atómica) y devuelve el valor."""
        ...
