from app.modules.vision.domain.entities import ImageAnalysis, Tag
from app.modules.vision.domain.errors import VisionUnavailableError

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class FakeAnalyzer:
    """Analizador en memoria: cuenta llamadas y puede simular caída."""

    def __init__(self, down: bool = False) -> None:
        self.down = down
        self.calls: list[tuple[int, str]] = []

    async def analyze(self, image: bytes, content_type: str) -> ImageAnalysis:
        self.calls.append((len(image), content_type))
        if self.down:
            raise VisionUnavailableError
        return ImageAnalysis(
            ocr_lines=("EXITO", "TOTAL 45.900"),
            tags=(Tag("food", 0.93), Tag("pizza", 0.81)),
            caption="a plate of food",
        )
