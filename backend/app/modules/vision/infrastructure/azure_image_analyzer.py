import logging
from typing import Any

import httpx

from app.modules.vision.domain.entities import MAX_OCR_LINES, MAX_TAGS, ImageAnalysis, Tag
from app.modules.vision.domain.errors import VisionUnavailableError

logger = logging.getLogger(__name__)

API_VERSION = "2023-10-01"
ALLOWED_FEATURES = frozenset({"read", "tags", "caption"})
DEFAULT_FEATURES = "read,tags"


class AzureImageAnalyzer:
    """Llama a Azure AI Vision Image Analysis (REST). La clave nunca sale del servidor.

    `transport` permite sustituir la red en las pruebas (httpx.MockTransport). Nunca se
    registra la imagen, el texto leído, la clave ni el cuerpo de las respuestas.
    """

    def __init__(
        self,
        key: str | None,
        endpoint: str | None,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
        features: str = DEFAULT_FEATURES,
    ) -> None:
        self._key = key
        self._endpoint = endpoint.rstrip("/") if endpoint else None
        self._timeout = timeout_seconds
        self._transport = transport
        self._features = _clean_features(features)

    async def analyze(self, image: bytes, content_type: str) -> ImageAnalysis:
        if not self._key or not self._endpoint:
            logger.warning("Azure AI Vision no está configurado (faltan clave o endpoint).")
            raise VisionUnavailableError
        if not self._endpoint.startswith("https://"):
            logger.warning("El endpoint de Azure AI Vision debe usar https.")
            raise VisionUnavailableError
        url = f"{self._endpoint}/computervision/imageanalysis:analyze"
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as c:
                response = await c.post(
                    url,
                    params={"api-version": API_VERSION, "features": self._features},
                    headers={
                        "Ocp-Apim-Subscription-Key": self._key,
                        "Content-Type": "application/octet-stream",
                    },
                    content=image,
                )
        except httpx.HTTPError as exc:
            logger.warning("Fallo de red al analizar una imagen: %s", type(exc).__name__)
            raise VisionUnavailableError from None
        if response.status_code != 200:
            logger.warning("Azure AI Vision respondió %s.", response.status_code)
            raise VisionUnavailableError
        try:
            return _parse(response.json())
        except (ValueError, TypeError, KeyError, AttributeError):
            logger.warning("Azure AI Vision devolvió una respuesta con forma inesperada.")
            raise VisionUnavailableError from None


def _clean_features(raw: str) -> str:
    """Solo características conocidas: la configuración no puede colar parámetros arbitrarios."""
    chosen = [f.strip() for f in raw.split(",") if f.strip() in ALLOWED_FEATURES]
    return ",".join(dict.fromkeys(chosen)) or DEFAULT_FEATURES


def _parse(body: dict[str, Any]) -> ImageAnalysis:
    lines: list[str] = []
    for block in (body.get("readResult") or {}).get("blocks") or []:
        for line in block.get("lines") or []:
            text = str(line["text"]).strip()
            if text:
                lines.append(text)
    tags = tuple(
        Tag(name=str(t["name"]).lower(), confidence=float(t["confidence"]))
        for t in (body.get("tagsResult") or {}).get("values") or []
    )
    caption_text = (body.get("captionResult") or {}).get("text")
    return ImageAnalysis(
        ocr_lines=tuple(lines[:MAX_OCR_LINES]),
        tags=tags[:MAX_TAGS],
        caption=str(caption_text).strip() or None if caption_text else None,
    )
