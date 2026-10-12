import uuid
from datetime import datetime
from typing import Protocol

from app.modules.recurring.domain.entities import RecurringRule


class RecurringRuleRepository(Protocol):
    async def get(self, rule_id: uuid.UUID) -> RecurringRule | None:
        """Busca por id sin filtrar por usuario; el caso de uso decide si es del usuario."""

    async def add(self, rule: RecurringRule) -> None: ...

    async def update(self, rule: RecurringRule) -> None: ...

    async def mark_deleted(self, rule_id: uuid.UUID, at: datetime) -> None: ...


class CategoryLookup(Protocol):
    async def active_type(self, user_id: uuid.UUID, category_id: uuid.UUID) -> str | None:
        """Tipo de la categoría si es del usuario y está activa; si no, None."""


class PendingOccurrences(Protocol):
    """Lo implementa `transactions` sobre su propia tabla (HU09 regla 8)."""

    async def discard(self, user_id: uuid.UUID, rule_id: uuid.UUID, at: datetime) -> None:
        """Elimina (lógicamente) las ocurrencias de la regla que siguen por confirmar."""
