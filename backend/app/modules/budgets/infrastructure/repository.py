import uuid
from datetime import date, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budgets.domain.entities import Budget
from app.modules.budgets.infrastructure.models import BudgetModel


def _to_entity(row: BudgetModel) -> Budget:
    return Budget(
        id=row.id,
        user_id=row.user_id,
        category_id=row.category_id,
        amount_minor=row.amount_minor,
        effective_from=row.effective_from,
        created_at=row.created_at,
        deleted_at=row.deleted_at,
    )


class SqlBudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, budget_id: uuid.UUID) -> Budget | None:
        row = await self._s.get(BudgetModel, budget_id, populate_existing=True)
        return _to_entity(row) if row else None

    async def exists_active(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        effective_from: date,
        *,
        other_than: uuid.UUID,
    ) -> bool:
        found = await self._s.scalar(
            select(BudgetModel.id)
            .where(
                BudgetModel.user_id == user_id,
                BudgetModel.category_id == category_id,
                BudgetModel.effective_from == effective_from,
                BudgetModel.deleted_at.is_(None),
                BudgetModel.id != other_than,
            )
            .limit(1)
        )
        return found is not None

    async def add(self, budget: Budget) -> None:
        self._s.add(
            BudgetModel(
                id=budget.id,
                user_id=budget.user_id,
                category_id=budget.category_id,
                amount_minor=budget.amount_minor,
                effective_from=budget.effective_from,
                created_at=budget.created_at,
            )
        )
        await self._s.flush()

    async def update(self, budget: Budget) -> None:
        await self._s.execute(
            update(BudgetModel)
            .where(BudgetModel.id == budget.id, BudgetModel.user_id == budget.user_id)
            .values(
                category_id=budget.category_id,
                amount_minor=budget.amount_minor,
                effective_from=budget.effective_from,
            )
        )

    async def mark_deleted(self, budget_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(BudgetModel).where(BudgetModel.id == budget_id).values(deleted_at=at)
        )
