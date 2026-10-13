import uuid
from datetime import datetime
from typing import Protocol

from app.modules.transactions.domain.entities import Transaction


class TransactionRepository(Protocol):
    async def get(self, transaction_id: uuid.UUID) -> Transaction | None:
        """Busca por id sin filtrar por usuario; el caso de uso decide si es del usuario."""

    async def add(self, transaction: Transaction) -> None: ...

    async def update(self, transaction: Transaction) -> None:
        """Reemplaza los campos editables y `deleted_at` (permite revivir un borrado)."""

    async def mark_deleted(self, transaction_id: uuid.UUID, at: datetime) -> None: ...


class CategoryLookup(Protocol):
    async def active_type(self, user_id: uuid.UUID, category_id: uuid.UUID) -> str | None:
        """Tipo de la categoría si es del usuario y está activa; si no, None."""


class RecurringRuleLookup(Protocol):
    async def state(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> str | None:
        """`active` o `deleted` si la regla es del usuario; None si no existe o es ajena."""
