import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime

from app.modules.budgets.application.ports import BudgetRepository, CategoryLookup
from app.modules.budgets.domain.entities import Budget
from app.modules.budgets.domain.errors import (
    BudgetNotFoundError,
    DuplicateBudgetError,
    InvalidCategoryError,
    NotExpenseCategoryError,
)
from app.modules.budgets.domain.rules import EXPENSE, validate_amount, validate_effective_from


@dataclass(frozen=True)
class UpsertBudgetInput:
    id: uuid.UUID
    category_id: uuid.UUID
    amount_minor: int
    effective_from: date
    created_at: datetime


class UpsertBudget:
    """Crea o cambia un presupuesto mensual (HU14).

    Cambiar el monto "desde un mes" es crear otro registro con ese `effective_from`; los meses
    anteriores conservan el suyo (regla 2). No confirma la transacción.
    """

    def __init__(self, budgets: BudgetRepository, categories: CategoryLookup) -> None:
        self._budgets = budgets
        self._categories = categories

    async def execute(self, user_id: uuid.UUID, data: UpsertBudgetInput) -> None:
        existing = await self._budgets.get(data.id)
        if existing is not None and (existing.user_id != user_id or existing.deleted_at):
            raise BudgetNotFoundError

        amount = validate_amount(data.amount_minor)
        effective_from = validate_effective_from(data.effective_from)

        category_type = await self._categories.active_type(user_id, data.category_id)
        if category_type is None:
            raise InvalidCategoryError
        if category_type != EXPENSE:
            raise NotExpenseCategoryError

        if await self._budgets.exists_active(
            user_id, data.category_id, effective_from, other_than=data.id
        ):
            raise DuplicateBudgetError

        if existing is None:
            await self._budgets.add(
                Budget(
                    id=data.id,
                    user_id=user_id,
                    category_id=data.category_id,
                    amount_minor=amount,
                    effective_from=effective_from,
                    created_at=data.created_at,
                )
            )
        else:
            await self._budgets.update(
                replace(
                    existing,
                    category_id=data.category_id,
                    amount_minor=amount,
                    effective_from=effective_from,
                )
            )
