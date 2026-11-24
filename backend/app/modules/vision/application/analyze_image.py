import uuid

from app.modules.vision.application.ports import ImageAnalyzer, RequestCounter
from app.modules.vision.domain.entities import (
    ALLOWED_CONTENT_TYPES,
    ImageAnalysis,
    detect_image_type,
)
from app.modules.vision.domain.errors import (
    EmptyImageError,
    ImageTooLargeError,
    UnsupportedImageError,
    VisionRateLimitError,
)

DEFAULT_MAX_PER_WINDOW = 30
WINDOW_SECONDS = 3600


class AnalyzeImage:
    """Analiza la imagen de un recibo o compra para el usuario autenticado (HU20).

    Valida tamaño y tipo ANTES de gastar cuota. El contador sube antes de llamar al
    proveedor: un intento que termina en 503 también consume cuota (igual que en voz).
    La imagen se procesa en memoria y se descarta.
    """

    def __init__(
        self,
        analyzer: ImageAnalyzer,
        counter: RequestCounter,
        max_bytes: int,
        max_per_window: int = DEFAULT_MAX_PER_WINDOW,
    ) -> None:
        self._analyzer = analyzer
        self._counter = counter
        self._max_bytes = max_bytes
        self._max_per_window = max_per_window

    async def execute(self, user_id: uuid.UUID, image: bytes, content_type: str) -> ImageAnalysis:
        if not image:
            raise EmptyImageError
        if len(image) > self._max_bytes:
            raise ImageTooLargeError
        real_type = detect_image_type(image)
        if content_type not in ALLOWED_CONTENT_TYPES or real_type != content_type:
            raise UnsupportedImageError
        count = await self._counter.incr(f"vision:analyze:{user_id}", WINDOW_SECONDS)
        if count > self._max_per_window:
            raise VisionRateLimitError
        return await self._analyzer.analyze(image, real_type)
