from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Response

from app.modules.auth.api.deps import CurrentUserId
from app.modules.speech.api.deps import get_issue_speech_token
from app.modules.speech.api.schemas import ErrorOut, SpeechTokenIn, SpeechTokenOut
from app.modules.speech.application.issue_token import IssueSpeechToken

router = APIRouter(prefix="/speech", tags=["speech"])

_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorOut, "description": "Sesión ausente o vencida."},
    422: {"description": "El cuerpo trae campos no permitidos."},
    429: {
        "model": ErrorOut,
        "description": "Más de 30 tokens en la última hora (code SPEECH_RATE_LIMITED).",
    },
    503: {
        "model": ErrorOut,
        "description": "Azure AI Speech no configurado o caído (code SPEECH_SERVICE_UNAVAILABLE).",
    },
}


@router.post(
    "/token",
    response_model=SpeechTokenOut,
    responses=_ERRORS,
    summary="Emitir token temporal de voz",
    description=(
        "Devuelve un token temporal de Azure AI Speech para el reconocimiento (HU17) y la "
        "síntesis (HU18, HU19) en el navegador, sin exponer la clave de suscripción (HU16)."
    ),
)
async def issue_speech_token(
    response: Response,
    user_id: CurrentUserId,
    use_case: Annotated[IssueSpeechToken, Depends(get_issue_speech_token)],
    _body: Annotated[SpeechTokenIn | None, Body()] = None,
) -> SpeechTokenOut:
    token = await use_case.execute(user_id)
    response.headers["Cache-Control"] = "no-store"
    return SpeechTokenOut(
        token=token.token, region=token.region, expires_in_seconds=token.expires_in_seconds
    )
