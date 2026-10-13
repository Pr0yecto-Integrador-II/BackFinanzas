import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import RefreshToken, User
from app.modules.auth.domain.errors import EmailAlreadyRegisteredError
from app.modules.auth.infrastructure.models import (
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserModel,
)


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, user: User) -> None:
        self._s.add(
            UserModel(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                currency=user.currency,
            )
        )
        try:
            await self._s.flush()
        except IntegrityError:  # dos registros simultáneos con el mismo correo
            raise EmailAlreadyRegisteredError from None

    async def get_by_email(self, email: str) -> User | None:
        row = await self._s.scalar(select(UserModel).where(UserModel.email == email))
        return _to_user(row)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return _to_user(await self._s.get(UserModel, user_id))

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> None:
        await self._s.execute(
            update(UserModel).where(UserModel.id == user_id).values(password_hash=password_hash)
        )


def _to_user(row: UserModel | None) -> User | None:
    if row is None:
        return None
    return User(row.id, row.email, row.password_hash, row.currency)


class SqlRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, token: RefreshToken) -> None:
        self._s.add(
            RefreshTokenModel(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                family_id=token.family_id,
                expires_at=token.expires_at,
            )
        )
        await self._s.flush()

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        # FOR UPDATE: dos refresh simultáneos del mismo token se serializan.
        row = await self._s.scalar(
            select(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .with_for_update()
        )
        if row is None:
            return None
        return RefreshToken(
            row.id, row.user_id, row.token_hash, row.family_id, row.expires_at, row.revoked_at
        )

    async def revoke(self, token_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(RefreshTokenModel).where(RefreshTokenModel.id == token_id).values(revoked_at=at)
        )

    async def revoke_family(self, family_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == family_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=at)
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=at)
        )


class SqlPasswordResetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def invalidate_unused(self, user_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.user_id == user_id,
                PasswordResetTokenModel.used_at.is_(None),
            )
            .values(used_at=at)
        )

    async def add(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> None:
        self._s.add(
            PasswordResetTokenModel(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        )
        await self._s.flush()

    async def consume(self, token_hash: str, now: datetime) -> uuid.UUID | None:
        # Un solo UPDATE condicional: si dos peticiones usan el enlace a la vez, solo una gana.
        result = await self._s.execute(
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.token_hash == token_hash,
                PasswordResetTokenModel.used_at.is_(None),
                PasswordResetTokenModel.expires_at > now,
            )
            .values(used_at=now)
            .returning(PasswordResetTokenModel.user_id)
        )
        return result.scalar_one_or_none()
