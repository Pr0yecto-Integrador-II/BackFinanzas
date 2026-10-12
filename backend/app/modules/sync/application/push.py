import uuid
from dataclasses import dataclass
from typing import Any

from app.modules.sync.application.ports import ChangeHandler, ChangesSource, Savepoint, UserLock
from app.shared.errors import DomainError
from app.shared.uow import UnitOfWork

# Orden en que se aplican (D-12): las claves foráneas deben existir.
ENTITY_ORDER = ("category", "recurring_rule", "transaction", "budget")


@dataclass(frozen=True)
class Change:
    entity: str
    op: str  # "upsert" | "delete"
    id: uuid.UUID
    data: dict[str, Any]


@dataclass(frozen=True)
class Rejection:
    id: uuid.UUID
    code: str
    message: str


@dataclass(frozen=True)
class PushResult:
    applied: list[uuid.UUID]
    rejected: list[Rejection]
    version: int


class PushChanges:
    """Aplica un lote de cambios del dispositivo (D-10, D-11, D-12).

    Primero todos los upserts (categorías → reglas → movimientos → presupuestos) y después los
    borrados en orden inverso, así un borrado de categoría ve ya los movimientos que el mismo
    lote movió o creó. Cada cambio va en su savepoint: uno inválido no tumba el lote.
    """

    def __init__(
        self,
        handlers: dict[str, ChangeHandler],
        savepoint: Savepoint,
        lock: UserLock,
        sources: list[ChangesSource],
        uow: UnitOfWork,
    ) -> None:
        self._handlers = handlers
        self._savepoint = savepoint
        self._lock = lock
        self._sources = sources
        self._uow = uow

    async def execute(self, user_id: uuid.UUID, changes: list[Change]) -> PushResult:
        await self._lock.acquire(user_id)
        applied: list[uuid.UUID] = []
        rejected: list[Rejection] = []
        for change in _ordered(changes):
            try:
                async with self._savepoint.scope():
                    await self._apply(user_id, change)
            except DomainError as exc:
                rejected.append(Rejection(change.id, exc.code, exc.message))
            else:
                applied.append(change.id)
        version = max([await s.max_version(user_id) for s in self._sources], default=0)
        await self._uow.commit()
        return PushResult(applied, rejected, version)

    async def _apply(self, user_id: uuid.UUID, change: Change) -> None:
        handler = self._handlers[change.entity]
        if change.op == "delete":
            await handler.delete(user_id, change.id, change.data)
        else:
            await handler.upsert(user_id, change.id, change.data)


def _ordered(changes: list[Change]) -> list[Change]:
    rank = {name: i for i, name in enumerate(ENTITY_ORDER)}
    upserts = sorted((c for c in changes if c.op != "delete"), key=lambda c: rank[c.entity])
    deletes = sorted((c for c in changes if c.op == "delete"), key=lambda c: -rank[c.entity])
    return upserts + deletes
