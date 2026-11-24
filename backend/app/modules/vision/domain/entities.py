from dataclasses import dataclass

ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})
MAX_OCR_LINES = 200
MAX_TAGS = 30


@dataclass(frozen=True)
class Tag:
    name: str
    confidence: float


@dataclass(frozen=True)
class ImageAnalysis:
    """Lo que el servicio de visión leyó de la imagen (HU20). No se guarda en ningún sitio."""

    ocr_lines: tuple[str, ...]
    tags: tuple[Tag, ...]
    caption: str | None

    def __repr__(self) -> str:  # el texto leído es dato sensible: nunca a logs ni trazas
        return f"ImageAnalysis(ocr_lines={len(self.ocr_lines)}, tags={len(self.tags)})"


def detect_image_type(data: bytes) -> str | None:
    """Tipo real según los primeros bytes; la cabecera `Content-Type` no basta."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None
