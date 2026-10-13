import uuid
from datetime import datetime
from typing import Protocol

from app.modules.auth.domain.entities import RefreshToken, User


class UserRepository(Protocol):
    async def add(self, user: User) -> None:
        """Lanza EmailAlreadyRegisteredError si el correo ya existe."""

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> None: ...


class RefreshTokenRepository(Protocol):
    async def add(self, token: RefreshToken) -> None: ...

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None: ...

    async def revoke(self, token_id: uuid.UUID, at: datetime) -> None: ...

    async def revoke_family(self, family_id: uuid.UUID, at: datetime) -> None: ...

    async def revoke_all_for_user(self, user_id: uuid.UUID, at: datetime) -> None: ...


class PasswordResetRepository(Protocol):
    async def invalidate_unused(self, user_id: uuid.UUID, at: datetime) -> None: ...

    async def add(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> None: ...

    async def consume(self, token_hash: str, now: datetime) -> uuid.UUID | None:
        """Marca el token como usado y devuelve su usuario, solo si sigue vigente."""


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...

    async def verify(self, password: str, hashed: str | None) -> bool:
        """Con `hashed=None` verifica contra un hash falso, para igualar el tiempo de respuesta."""


class AccessTokenService(Protocol):
    def issue(self, user_id: uuid.UUID) -> str: ...

    def decode(self, token: str) -> uuid.UUID:
        """Lanza InvalidSessionError si el token no es válido o venció."""


class SecureTokens(Protocol):
    def generate(self) -> str: ...

    def hash(self, raw: str) -> str: ...


class RateLimiter(Protocol):
    async def incr(self, key: str, window_seconds: int) -> int:
        """Suma 1 al contador de la ventana y devuelve el valor."""

    async def reset(self, key: str) -> None: ...

    async def set_flag(self, key: str, seconds: int) -> None: ...

    async def has_flag(self, key: str) -> bool: ...


class PasswordResetMailer(Protocol):
    async def send(self, email: str, token: str) -> None: ...


class DefaultCategoriesSeeder(Protocol):
    async def seed(self, user_id: uuid.UUID) -> None:
        """Crea las 12 categorías predeterminadas (HU01) en la transacción en curso."""
