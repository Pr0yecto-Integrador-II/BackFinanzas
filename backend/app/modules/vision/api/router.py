from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response

from app.config import Settings
from app.modules.auth.api.deps import CurrentUserId, SettingsDep
from app.modules.vision.api.deps import get_analyze_image
from app.modules.vision.api.schemas import ErrorOut, ImageAnalysisOut, TagOut
from app.modules.vision.application.analyze_image import AnalyzeImage
from app.modules.vision.domain.errors import ImageTooLargeError

router = APIRouter(prefix="/vision", tags=["vision"])

_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorOut, "description": "Sesión ausente o vencida."},
    413: {"model": ErrorOut, "description": "La imagen supera el tamaño máximo (IMAGE_TOO_LARGE)."},
    415: {
        "model": ErrorOut,
        "description": "No es una imagen JPEG o PNG (UNSUPPORTED_IMAGE, EMPTY_IMAGE).",
    },
    429: {
        "model": ErrorOut,
        "description": "Límite de análisis por hora superado (VISION_RATE_LIMITED).",
    },
    503: {
        "model": ErrorOut,
        "description": "Servicio de visión no configurado o caído (VISION_SERVICE_UNAVAILABLE).",
    },
}


async def _read_limited(request: Request, settings: Settings) -> bytes:
    """Lee el cuerpo sin pasar del máximo: rechaza antes de acumular una imagen enorme."""
    limit = settings.vision_max_image_bytes
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > limit:
        raise ImageTooLargeError
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > limit:
            raise ImageTooLargeError
    return bytes(data)


@router.post(
    "/analyze",
    response_model=ImageAnalysisOut,
    responses=_ERRORS,
    summary="Analizar la imagen de un recibo o una compra",
    description=(
        "El cuerpo es la imagen cruda (`Content-Type: image/jpeg` o `image/png`). Devuelve el "
        "texto leído, las etiquetas y una descripción. No guarda la imagen ni el resultado "
        "(HU20)."
    ),
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "image/jpeg": {"schema": {"type": "string", "format": "binary"}},
                "image/png": {"schema": {"type": "string", "format": "binary"}},
            },
        }
    },
)
async def analyze_image(
    request: Request,
    response: Response,
    user_id: CurrentUserId,
    settings: SettingsDep,
    use_case: Annotated[AnalyzeImage, Depends(get_analyze_image)],
) -> ImageAnalysisOut:
    image = await _read_limited(request, settings)
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    result = await use_case.execute(user_id, image, content_type)
    response.headers["Cache-Control"] = "no-store"
    return ImageAnalysisOut(
        ocr_lines=list(result.ocr_lines),
        tags=[TagOut(name=t.name, confidence=t.confidence) for t in result.tags],
        caption=result.caption,
    )
