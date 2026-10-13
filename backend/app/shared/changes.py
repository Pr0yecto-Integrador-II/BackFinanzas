"""Lectura de cambios para el pull (D-13): cada módulo la implementa sobre su propia tabla."""

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class PulledChange:
    entity: str
    id: uuid.UUID
    version: int
    data: dict[str, Any]
    deleted: bool


class ModelChangesSource:
    """Cambios de una tabla sincronizable, filtrados siempre por `user_id`."""

    def __init__(
        self,
        session: AsyncSession,
        entity: str,
        model: Any,
        fields: tuple[str, ...],
    ) -> None:
        self._s = session
        self._entity = entity
        self._model = model
        self._fields = fields

    async def since(self, user_id: uuid.UUID, since: int, limit: int) -> list[PulledChange]:
        m = self._model
        rows = await self._s.scalars(
            select(m)
            .where(m.user_id == user_id, m.version > since)
            .order_by(m.version)
            .limit(limit)
            .execution_options(populate_existing=True)
        )
        return [
            PulledChange(
                entity=self._entity,
                id=r.id,
                version=r.version,
                data={f: getattr(r, f) for f in self._fields},
                deleted=r.deleted_at is not None,
            )
            for r in rows
        ]

    async def max_version(self, user_id: uuid.UUID) -> int:
        m = self._model
        value = await self._s.scalar(select(func.max(m.version)).where(m.user_id == user_id))
        return int(value or 0)
