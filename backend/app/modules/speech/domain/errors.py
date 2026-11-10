from app.shared.errors import ServiceUnavailableError, TooManyRequestsError


class SpeechUnavailableError(ServiceUnavailableError):
    """Azure AI Speech no está configurado o no respondió (HU16 regla 4). HTTP 503."""

    message = "El servicio de voz no está disponible en este momento"

    @property
    def code(self) -> str:
        return "SPEECH_SERVICE_UNAVAILABLE"


class SpeechRateLimitError(TooManyRequestsError):
    """Se superó el límite de tokens de voz por usuario (HU16 regla 3). HTTP 429."""

    message = "Has alcanzado el límite temporal del servicio de voz. Intenta más tarde"

    @property
    def code(self) -> str:
        return "SPEECH_RATE_LIMITED"
