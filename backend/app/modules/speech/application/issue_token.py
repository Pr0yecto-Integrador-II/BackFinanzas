import uuid

from app.modules.speech.application.ports import RequestCounter, SpeechTokenProvider
from app.modules.speech.domain.entities import SpeechToken
from app.modules.speech.domain.errors import SpeechRateLimitError

MAX_TOKENS_PER_WINDOW = 30
WINDOW_SECONDS = 3600


class IssueSpeechToken:
    """Emite un token temporal de voz para el usuario autenticado (HU16).

    El contador sube ANTES de llamar al proveedor: un intento que termina en 503 también
    consume cuota, así un cliente que reintenta en bucle no puede saturar Azure (HU19).
    """

    def __init__(self, provider: SpeechTokenProvider, counter: RequestCounter) -> None:
        self._provider = provider
        self._counter = counter

    async def execute(self, user_id: uuid.UUID) -> SpeechToken:
        count = await self._counter.incr(f"speech:token:{user_id}", WINDOW_SECONDS)
        if count > MAX_TOKENS_PER_WINDOW:
            raise SpeechRateLimitError
        return await self._provider.issue()
