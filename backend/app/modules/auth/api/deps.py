import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition import create_default_categories
from app.config import Settings, get_settings
from app.container import get_arq_pool, get_clock, get_redis
from app.modules.auth.application import ports
from app.modules.auth.application.login import LoginUser
from app.modules.auth.application.logout import LogoutUser
from app.modules.auth.application.me import GetMe
from app.modules.auth.application.password_reset import RequestPasswordReset, ResetPassword
from app.modules.auth.application.refresh import RefreshSession
from app.modules.auth.application.register import RegisterUser
from app.modules.auth.application.sessions import IssueSession
from app.modules.auth.domain.errors import InvalidSessionError
from app.modules.auth.infrastructure.categories_seeder import CategoriesSeeder
from app.modules.auth.infrastructure.mailer import ArqPasswordResetMailer
from app.modules.auth.infrastructure.rate_limiter import RedisRateLimiter
from app.modules.auth.infrastructure.repositories import (
    SqlPasswordResetRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.modules.auth.infrastructure.security import Argon2Hasher, JwtAccessTokens, Sha256Tokens
from app.shared.clock import Clock
from app.shared.db import get_session
from app.shared.sql_uow import SqlAlchemyUnitOfWork
from app.shared.uow import UnitOfWork

REFRESH_COOKIE = "refresh_token"

SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]

_hasher = Argon2Hasher()
_secure = Sha256Tokens()


def get_uow(session: SessionDep) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(session)


def get_users(session: SessionDep) -> ports.UserRepository:
    return SqlUserRepository(session)


def get_refresh_tokens(session: SessionDep) -> ports.RefreshTokenRepository:
    return SqlRefreshTokenRepository(session)


def get_resets(session: SessionDep) -> ports.PasswordResetRepository:
    return SqlPasswordResetRepository(session)


def get_hasher() -> ports.PasswordHasher:
    return _hasher


def get_secure_tokens() -> ports.SecureTokens:
    return _secure


def get_access_tokens(settings: SettingsDep, clock: ClockDep) -> ports.AccessTokenService:
    return JwtAccessTokens(settings.jwt_secret, settings.access_token_minutes, clock)


def get_limiter() -> ports.RateLimiter:
    return RedisRateLimiter(get_redis())


async def get_mailer(settings: SettingsDep) -> ports.PasswordResetMailer:
    return ArqPasswordResetMailer(await get_arq_pool(), settings.frontend_url)


def get_seeder(session: SessionDep, clock: ClockDep) -> ports.DefaultCategoriesSeeder:
    return CategoriesSeeder(create_default_categories(session, clock))


Users = Annotated[ports.UserRepository, Depends(get_users)]
Tokens = Annotated[ports.RefreshTokenRepository, Depends(get_refresh_tokens)]
Resets = Annotated[ports.PasswordResetRepository, Depends(get_resets)]
Hasher = Annotated[ports.PasswordHasher, Depends(get_hasher)]
Secure = Annotated[ports.SecureTokens, Depends(get_secure_tokens)]
Access = Annotated[ports.AccessTokenService, Depends(get_access_tokens)]
Limiter = Annotated[ports.RateLimiter, Depends(get_limiter)]
Mailer = Annotated[ports.PasswordResetMailer, Depends(get_mailer)]
Seeder = Annotated[ports.DefaultCategoriesSeeder, Depends(get_seeder)]
Uow = Annotated[UnitOfWork, Depends(get_uow)]


def get_issue_session(
    tokens: Tokens, access: Access, secure: Secure, clock: ClockDep, settings: SettingsDep
) -> IssueSession:
    return IssueSession(tokens, access, secure, clock, settings.refresh_token_days)


Issue = Annotated[IssueSession, Depends(get_issue_session)]


def get_register(
    users: Users, hasher: Hasher, seeder: Seeder, issue: Issue, uow: Uow
) -> RegisterUser:
    return RegisterUser(users, hasher, seeder, issue, uow)


def get_login(users: Users, hasher: Hasher, limiter: Limiter, issue: Issue, uow: Uow) -> LoginUser:
    return LoginUser(users, hasher, limiter, issue, uow)


def get_refresh(
    users: Users, tokens: Tokens, secure: Secure, issue: Issue, clock: ClockDep, uow: Uow
) -> RefreshSession:
    return RefreshSession(users, tokens, secure, issue, clock, uow)


def get_logout(tokens: Tokens, secure: Secure, clock: ClockDep, uow: Uow) -> LogoutUser:
    return LogoutUser(tokens, secure, clock, uow)


def get_request_reset(
    users: Users,
    resets: Resets,
    secure: Secure,
    limiter: Limiter,
    mailer: Mailer,
    clock: ClockDep,
    uow: Uow,
) -> RequestPasswordReset:
    return RequestPasswordReset(users, resets, secure, limiter, mailer, clock, uow)


def get_reset(
    users: Users,
    resets: Resets,
    tokens: Tokens,
    hasher: Hasher,
    secure: Secure,
    clock: ClockDep,
    uow: Uow,
) -> ResetPassword:
    return ResetPassword(users, resets, tokens, hasher, secure, clock, uow)


def get_me(users: Users) -> GetMe:
    return GetMe(users)


_bearer = HTTPBearer(auto_error=False)


def current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    access: Access,
) -> uuid.UUID:
    """El `user_id` sale SIEMPRE del token, nunca del cuerpo ni de la URL."""
    if credentials is None:
        raise InvalidSessionError
    return access.decode(credentials.credentials)


CurrentUserId = Annotated[uuid.UUID, Depends(current_user_id)]


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
