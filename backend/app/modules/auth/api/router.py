from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response, status

from app.config import Settings
from app.modules.auth.api import deps
from app.modules.auth.api.schemas import (
    ForgotPasswordIn,
    LoginIn,
    MessageOut,
    RegisterIn,
    ResetPasswordIn,
    SessionOut,
    UserOut,
)
from app.modules.auth.application.login import LoginInput, LoginUser
from app.modules.auth.application.logout import LogoutUser
from app.modules.auth.application.me import GetMe
from app.modules.auth.application.password_reset import (
    RequestPasswordReset,
    ResetPassword,
    ResetPasswordInput,
)
from app.modules.auth.application.refresh import RefreshSession
from app.modules.auth.application.register import RegisterInput, RegisterUser
from app.modules.auth.application.sessions import Session

router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["auth"])

RefreshCookie = Annotated[
    str | None, Cookie(alias=deps.REFRESH_COOKIE)
]  # opcional: sin cookie -> 401


def _set_cookie(response: Response, session: Session, settings: Settings) -> None:
    response.set_cookie(
        deps.REFRESH_COOKIE,
        session.refresh_token,
        max_age=session.refresh_max_age_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/auth",  # solo viaja a los endpoints de auth
    )


def _session_out(session: Session) -> SessionOut:
    u = session.user
    return SessionOut(
        access_token=session.access_token, user=UserOut(id=u.id, email=u.email, currency=u.currency)
    )


@router.post("/register", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterIn,
    response: Response,
    settings: deps.SettingsDep,
    use_case: Annotated[RegisterUser, Depends(deps.get_register)],
) -> SessionOut:
    session = await use_case.execute(
        RegisterInput(body.email, body.password, body.password_confirmation, body.currency)
    )
    _set_cookie(response, session, settings)
    return _session_out(session)


@router.post("/login", response_model=SessionOut)
async def login(
    body: LoginIn,
    response: Response,
    settings: deps.SettingsDep,
    ip: Annotated[str, Depends(deps.client_ip)],
    use_case: Annotated[LoginUser, Depends(deps.get_login)],
) -> SessionOut:
    session = await use_case.execute(LoginInput(body.email, body.password, ip))
    _set_cookie(response, session, settings)
    return _session_out(session)


@router.post("/refresh", response_model=SessionOut)
async def refresh(
    response: Response,
    settings: deps.SettingsDep,
    use_case: Annotated[RefreshSession, Depends(deps.get_refresh)],
    refresh_token: RefreshCookie = None,
) -> SessionOut:
    session = await use_case.execute(refresh_token)
    _set_cookie(response, session, settings)
    return _session_out(session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    use_case: Annotated[LogoutUser, Depends(deps.get_logout)],
    refresh_token: RefreshCookie = None,
    all: Annotated[bool, Query()] = False,  # noqa: A002  (nombre fijado por el Blueprint)
) -> None:
    await use_case.execute(refresh_token, everywhere=all)
    response.delete_cookie(deps.REFRESH_COOKIE, path="/auth")


@router.post("/password/forgot", response_model=MessageOut)
async def forgot_password(
    body: ForgotPasswordIn,
    use_case: Annotated[RequestPasswordReset, Depends(deps.get_request_reset)],
) -> MessageOut:
    await use_case.execute(body.email)
    return MessageOut(message="Si el correo está registrado, recibirás un enlace en unos minutos.")


@router.post("/password/reset", response_model=MessageOut)
async def reset_password(
    body: ResetPasswordIn,
    use_case: Annotated[ResetPassword, Depends(deps.get_reset)],
) -> MessageOut:
    await use_case.execute(
        ResetPasswordInput(body.token, body.password, body.password_confirmation)
    )
    return MessageOut(message="Contraseña actualizada.")


@me_router.get("/me", response_model=UserOut)
async def me(
    user_id: deps.CurrentUserId,
    use_case: Annotated[GetMe, Depends(deps.get_me)],
) -> UserOut:
    user = await use_case.execute(user_id)
    return UserOut(id=user.id, email=user.email, currency=user.currency)
