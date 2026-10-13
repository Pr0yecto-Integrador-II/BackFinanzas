from app.modules.auth.application.ports import RefreshTokenRepository, SecureTokens
from app.shared.clock import Clock
from app.shared.uow import UnitOfWork


class LogoutUser:
    """Cierra la sesión del token dado, o todas las del usuario con `everywhere=True`.

    Es idempotente: un token desconocido no es un error. Usa el refresh token (cookie) y no el
    access token porque este último puede haber vencido mientras la app estuvo sin conexión.
    """

    def __init__(
        self,
        refresh_tokens: RefreshTokenRepository,
        secure: SecureTokens,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._secure = secure
        self._clock = clock
        self._uow = uow

    async def execute(self, raw_token: str | None, everywhere: bool = False) -> None:
        if not raw_token:
            return
        token = await self._refresh_tokens.get_by_hash_for_update(self._secure.hash(raw_token))
        if token is None:
            return
        now = self._clock.now()
        if everywhere:
            await self._refresh_tokens.revoke_all_for_user(token.user_id, now)
        else:
            await self._refresh_tokens.revoke_family(token.family_id, now)
        await self._uow.commit()
