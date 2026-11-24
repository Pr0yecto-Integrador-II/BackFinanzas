"""HU20: reglas del caso de uso (tipo, tamaño, cuota y degradación)."""

import uuid

import pytest

from app.modules.vision.application.analyze_image import (
    DEFAULT_MAX_PER_WINDOW,
    WINDOW_SECONDS,
    AnalyzeImage,
)
from app.modules.vision.domain.errors import (
    EmptyImageError,
    ImageTooLargeError,
    UnsupportedImageError,
    VisionRateLimitError,
    VisionUnavailableError,
)
from tests.unit.auth.fakes import FakeLimiter
from tests.unit.vision.fakes import JPEG, PNG, FakeAnalyzer

MAX = 1000


def _use_case(
    down: bool = False, limit: int = DEFAULT_MAX_PER_WINDOW
) -> tuple[AnalyzeImage, FakeAnalyzer, FakeLimiter]:
    analyzer, limiter = FakeAnalyzer(down=down), FakeLimiter()
    return AnalyzeImage(analyzer, limiter, MAX, limit), analyzer, limiter


async def test_analiza_jpeg_y_png() -> None:
    use_case, analyzer, _ = _use_case()
    user = uuid.uuid4()
    jpeg = await use_case.execute(user, JPEG, "image/jpeg")
    await use_case.execute(user, PNG, "image/png")
    assert jpeg.ocr_lines == ("EXITO", "TOTAL 45.900")
    assert [t.name for t in jpeg.tags] == ["food", "pizza"]
    assert [c[1] for c in analyzer.calls] == ["image/jpeg", "image/png"]


async def test_imagen_vacia_se_rechaza_sin_gastar_cuota() -> None:
    use_case, analyzer, limiter = _use_case()
    with pytest.raises(EmptyImageError) as exc:
        await use_case.execute(uuid.uuid4(), b"", "image/jpeg")
    assert exc.value.code == "EMPTY_IMAGE"
    assert analyzer.calls == [] and limiter.counters == {}


async def test_imagen_demasiado_grande_se_rechaza_sin_gastar_cuota() -> None:
    use_case, analyzer, limiter = _use_case()
    with pytest.raises(ImageTooLargeError) as exc:
        await use_case.execute(uuid.uuid4(), JPEG + b"\x00" * MAX, "image/jpeg")
    assert exc.value.code == "IMAGE_TOO_LARGE"
    assert analyzer.calls == [] and limiter.counters == {}


@pytest.mark.parametrize(
    ("data", "declared"),
    [
        (b"%PDF-1.7 no soy una imagen", "image/jpeg"),  # contenido falso
        (PNG, "image/jpeg"),  # la cabecera miente
        (JPEG, "image/gif"),  # tipo no admitido
        (JPEG, ""),  # sin tipo
    ],
)
async def test_tipo_no_admitido_se_rechaza_sin_gastar_cuota(data: bytes, declared: str) -> None:
    use_case, analyzer, limiter = _use_case()
    with pytest.raises(UnsupportedImageError) as exc:
        await use_case.execute(uuid.uuid4(), data, declared)
    assert exc.value.code == "UNSUPPORTED_IMAGE"
    assert analyzer.calls == [] and limiter.counters == {}


async def test_la_cuota_por_hora_es_por_usuario() -> None:
    assert (DEFAULT_MAX_PER_WINDOW, WINDOW_SECONDS) == (30, 3600)
    use_case, analyzer, limiter = _use_case(limit=3)
    ana, luis = uuid.uuid4(), uuid.uuid4()
    for _ in range(3):
        await use_case.execute(ana, JPEG, "image/jpeg")
    with pytest.raises(VisionRateLimitError) as exc:
        await use_case.execute(ana, JPEG, "image/jpeg")
    assert exc.value.code == "VISION_RATE_LIMITED"
    assert len(analyzer.calls) == 3  # el intento 4 no llega al proveedor
    assert limiter.counters[f"vision:analyze:{ana}"] == 4
    await use_case.execute(luis, JPEG, "image/jpeg")  # otro usuario, otra cuota


async def test_servicio_caido_responde_no_disponible_y_consume_cuota() -> None:
    use_case, _, limiter = _use_case(down=True)
    user = uuid.uuid4()
    with pytest.raises(VisionUnavailableError) as exc:
        await use_case.execute(user, JPEG, "image/jpeg")
    assert exc.value.code == "VISION_SERVICE_UNAVAILABLE"
    assert limiter.counters[f"vision:analyze:{user}"] == 1
