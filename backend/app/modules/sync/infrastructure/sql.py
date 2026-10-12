import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sync.domain.errors import StorageConflictError


class SqlSavepoint:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @asynccontextmanager
    async def scope(self) -> AsyncIterator[None]:
        try:
            async with self._s.begin_nested():
                yield
        except IntegrityError as exc:
            raise StorageConflictError from exc


class AdvisoryUserLock:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def acquire(self, user_id: uuid.UUID) -> None:
        await self._s.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:u, 0))"), {"u": str(user_id)}
        )
