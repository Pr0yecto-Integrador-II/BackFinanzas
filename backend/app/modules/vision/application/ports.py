from typing import Protocol

from app.modules.vision.domain.entities import ImageAnalysis


class ImageAnalyzer(Protocol):
    async def analyze(self, image: bytes, content_type: str) -> ImageAnalysis:
        """Lee la imagen con el proveedor. Lanza VisionUnavailableError si falla."""
        ...


class RequestCounter(Protocol):
    async def incr(self, key: str, window_seconds: int) -> int:
        """Suma 1 al contador de la ventana (de forma atómica) y devuelve el valor."""
        ...
