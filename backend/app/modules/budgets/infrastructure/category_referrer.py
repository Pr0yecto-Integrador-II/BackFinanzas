import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budgets.infrastructure.models import BudgetModel


class BudgetCategoryReferrer:
    """Responde a `categories` sobre el uso de una categoría en presupuestos (HU08 regla 5)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _has_active(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        found = await self._s.scalar(
            select(BudgetModel.id)
            .where(
                BudgetModel.user_id == user_id,
                BudgetModel.category_id == category_id,
                BudgetModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        return found is not None

    async def is_referenced(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        return await self._has_active(user_id, category_id)

    async def move(
        self, user_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID, at: datetime
    ) -> None:
        if await self._has_active(user_id, to_id):
            # Si ambas tenían presupuesto, se conserva el de la categoría destino.
            await self._s.execute(
                update(BudgetModel)
                .where(
                    BudgetModel.user_id == user_id,
                    BudgetModel.category_id == from_id,
                    BudgetModel.deleted_at.is_(None),
                )
                .values(deleted_at=at)
            )
        else:
            await self._s.execute(
                update(BudgetModel)
                .where(
                    BudgetModel.user_id == user_id,
                    BudgetModel.category_id == from_id,
                    BudgetModel.deleted_at.is_(None),
                )
                .values(category_id=to_id)
            )
