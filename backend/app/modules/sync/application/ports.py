import uuid
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from app.shared.changes import PulledChange


class ChangeHandler(Protocol):
    """Traduce un cambio del push al caso de uso del módulo dueño (D-13)."""

    async def upsert(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        """Lanza `DomainError` si el cambio no es válido."""

    async def delete(
        self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]
    ) -> None: ...


class Savepoint(Protocol):
    def scope(self) -> AbstractAsyncContextManager[None]:
        """Aísla un cambio: si falla, se revierte solo ese cambio (D-12)."""


class UserLock(Protocol):
    async def acquire(self, user_id: uuid.UUID) -> None:
        """Serializa los push de un usuario hasta el final de la transacción (D-10)."""


class ChangesSource(Protocol):
    async def since(self, user_id: uuid.UUID, since: int, limit: int) -> list[PulledChange]: ...

    async def max_version(self, user_id: uuid.UUID) -> int: ...
