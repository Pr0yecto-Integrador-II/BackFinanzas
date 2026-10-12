import uuid
from datetime import date, datetime
from typing import Protocol

from app.modules.budgets.domain.entities import Budget


class BudgetRepository(Protocol):
    async def get(self, budget_id: uuid.UUID) -> Budget | None:
        """Busca por id sin filtrar por usuario; el caso de uso decide si es del usuario."""

    async def exists_active(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        effective_from: date,
        *,
        other_than: uuid.UUID,
    ) -> bool:
        """¿Hay otro presupuesto activo de la categoría para ese mes?"""

    async def add(self, budget: Budget) -> None: ...

    async def update(self, budget: Budget) -> None: ...

    async def mark_deleted(self, budget_id: uuid.UUID, at: datetime) -> None: ...


class CategoryLookup(Protocol):
    async def active_type(self, user_id: uuid.UUID, category_id: uuid.UUID) -> str | None:
        """Tipo de la categoría si es del usuario y está activa; si no, None."""
