from dataclasses import dataclass
from datetime import timedelta

from app.modules.auth.application.ports import (
    PasswordHasher,
    PasswordResetMailer,
    PasswordResetRepository,
    RateLimiter,
    RefreshTokenRepository,
    SecureTokens,
    UserRepository,
)
from app.modules.auth.domain.errors import InvalidResetTokenError
from app.modules.auth.domain.rules import normalize_email, validate_password
from app.shared.clock import Clock
from app.shared.errors import DomainError
from app.shared.uow import UnitOfWork

RESET_TTL = timedelta(minutes=30)
MAX_REQUESTS_PER_HOUR = 3


class RequestPasswordReset:
    """Siempre termina igual exista o no la cuenta, o se haya superado el límite (HU03)."""

    def __init__(
        self,
        users: UserRepository,
        resets: PasswordResetRepository,
        secure: SecureTokens,
        limiter: RateLimiter,
        mailer: PasswordResetMailer,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._resets = resets
        self._secure = secure
        self._limiter = limiter
        self._mailer = mailer
        self._clock = clock
        self._uow = uow

    async def execute(self, raw_email: str) -> None:
        try:
            email = normalize_email(raw_email)
        except DomainError:
            return
        if await self._limiter.incr(f"reset:req:{email}", 3600) > MAX_REQUESTS_PER_HOUR:
            return
        user = await self._users.get_by_email(email)
        if user is None:
            return
        now = self._clock.now()
        raw = self._secure.generate()
        await self._resets.invalidate_unused(user.id, now)
        await self._resets.add(user.id, self._secure.hash(raw), now + RESET_TTL)
        await self._uow.commit()  # primero se guarda; el correo solo sale si el token existe
        await self._mailer.send(email, raw)


@dataclass(frozen=True)
class ResetPasswordInput:
    token: str
    password: str
    password_confirmation: str


class ResetPassword:
    def __init__(
        self,
        users: UserRepository,
        resets: PasswordResetRepository,
        refresh_tokens: RefreshTokenRepository,
        hasher: PasswordHasher,
        secure: SecureTokens,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._resets = resets
        self._refresh_tokens = refresh_tokens
        self._hasher = hasher
        self._secure = secure
        self._clock = clock
        self._uow = uow

    async def execute(self, data: ResetPasswordInput) -> None:
        validate_password(data.password, data.password_confirmation)
        now = self._clock.now()
        user_id = await self._resets.consume(self._secure.hash(data.token), now)
        if user_id is None:
            raise InvalidResetTokenError
        await self._users.update_password(user_id, await self._hasher.hash(data.password))
        await self._refresh_tokens.revoke_all_for_user(user_id, now)  # HU03 regla 6
        await self._uow.commit()
