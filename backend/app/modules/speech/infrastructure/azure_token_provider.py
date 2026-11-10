import logging

import httpx

from app.modules.speech.domain.entities import MAX_TOKEN_SECONDS, SpeechToken
from app.modules.speech.domain.errors import SpeechUnavailableError

logger = logging.getLogger(__name__)


class AzureSpeechTokenProvider:
    """Pide un token al STS de Azure AI Speech. La clave nunca sale del servidor.

    `transport` permite sustituir la red en las pruebas (httpx.MockTransport).
    """

    def __init__(
        self,
        key: str | None,
        region: str | None,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._key = key
        self._region = region
        self._timeout = timeout_seconds
        self._transport = transport

    async def issue(self) -> SpeechToken:
        if not self._key or not self._region:
            logger.warning("Azure AI Speech no está configurado (faltan clave o región).")
            raise SpeechUnavailableError
        url = f"https://{self._region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as c:
                response = await c.post(url, headers={"Ocp-Apim-Subscription-Key": self._key})
        except httpx.HTTPError as exc:
            # Solo el tipo de error: el mensaje podría incluir datos de la petición.
            logger.warning("Fallo de red al pedir token de voz: %s", type(exc).__name__)
            raise SpeechUnavailableError from None
        token = response.text.strip()
        if response.status_code != 200 or not token:
            logger.warning("Azure AI Speech respondió %s al pedir token.", response.status_code)
            raise SpeechUnavailableError
        return SpeechToken(token=token, region=self._region, expires_in_seconds=MAX_TOKEN_SECONDS)
