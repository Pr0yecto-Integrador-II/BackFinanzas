import asyncio
import hashlib
import secrets
import uuid
from datetime import timedelta

import jwt
from pwdlib import PasswordHash

from app.modules.auth.domain.errors import InvalidSessionError
from app.shared.clock import Clock


class Argon2Hasher:
    """Argon2id. Es CPU-intensivo, así que se ejecuta fuera del bucle de eventos."""

    def __init__(self) -> None:
        self._hash = PasswordHash.recommended()
        self._dummy: str | None = None

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hash.hash, password)

    async def verify(self, password: str, hashed: str | None) -> bool:
        if hashed is None:
            if self._dummy is None:
                self._dummy = await self.hash("contraseña-falsa-1")
            await asyncio.to_thread(self._hash.verify, password, self._dummy)
            return False
        return await asyncio.to_thread(self._hash.verify, password, hashed)


class JwtAccessTokens:
    _ALGORITHM = "HS256"

    def __init__(self, secret: str, minutes: int, clock: Clock) -> None:
        self._secret = secret
        self._ttl = timedelta(minutes=minutes)
        self._clock = clock

    def issue(self, user_id: uuid.UUID) -> str:
        now = self._clock.now()
        claims = {"sub": str(user_id), "iat": now, "exp": now + self._ttl}
        return jwt.encode(claims, self._secret, algorithm=self._ALGORITHM)

    def decode(self, token: str) -> uuid.UUID:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._ALGORITHM],
                options={"require": ["sub", "exp"]},
            )
            return uuid.UUID(claims["sub"])
        except (jwt.PyJWTError, ValueError):
            raise InvalidSessionError from None


class Sha256Tokens:
    def generate(self) -> str:
        return secrets.token_urlsafe(32)

    def hash(self, raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()
