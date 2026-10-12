from app.modules.auth.application.ports import (
    RefreshTokenRepository,
    SecureTokens,
    UserRepository,
)
from app.modules.auth.application.sessions import IssueSession, Session
from app.modules.auth.domain.errors import InvalidSessionError
from app.shared.clock import Clock
from app.shared.uow import UnitOfWork


class RefreshSession:
    """Rota el refresh token. Reusar uno ya rotado revoca toda la familia (posible robo)."""

    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        secure: SecureTokens,
        issue_session: IssueSession,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._secure = secure
        self._issue_session = issue_session
        self._clock = clock
        self._uow = uow

    async def execute(self, raw_token: str | None) -> Session:
        if not raw_token:
            raise InvalidSessionError
        now = self._clock.now()
        token = await self._refresh_tokens.get_by_hash_for_update(self._secure.hash(raw_token))
        if token is None:
            raise InvalidSessionError
        if token.revoked_at is not None:
            await self._refresh_tokens.revoke_family(token.family_id, now)
            await self._uow.commit()  # la revocación debe persistir aunque se rechace la petición
            raise InvalidSessionError
        if token.expires_at <= now:
            raise InvalidSessionError
        user = await self._users.get_by_id(token.user_id)
        if user is None:
            raise InvalidSessionError

        await self._refresh_tokens.revoke(token.id, now)
        session = await self._issue_session.execute(user, family_id=token.family_id)
        await self._uow.commit()
        return session
