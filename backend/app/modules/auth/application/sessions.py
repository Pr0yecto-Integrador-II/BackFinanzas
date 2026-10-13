import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.modules.auth.application.ports import (
    AccessTokenService,
    RefreshTokenRepository,
    SecureTokens,
)
from app.modules.auth.domain.entities import RefreshToken, User
from app.shared.clock import Clock


@dataclass(frozen=True)
class Session:
    user: User
    access_token: str
    refresh_token: str
    refresh_max_age_seconds: int


class IssueSession:
    """Crea el par de tokens de una sesión (una sesión = una familia de refresh tokens)."""

    def __init__(
        self,
        refresh_tokens: RefreshTokenRepository,
        access: AccessTokenService,
        secure: SecureTokens,
        clock: Clock,
        refresh_days: int,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._access = access
        self._secure = secure
        self._clock = clock
        self._days = refresh_days

    async def execute(self, user: User, family_id: uuid.UUID | None = None) -> Session:
        raw = self._secure.generate()
        ttl = timedelta(days=self._days)
        await self._refresh_tokens.add(
            RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=self._secure.hash(raw),
                family_id=family_id or uuid.uuid4(),
                expires_at=self._clock.now() + ttl,
            )
        )
        return Session(user, self._access.issue(user.id), raw, int(ttl.total_seconds()))
