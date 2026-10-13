import uuid

from app.modules.budgets.application.ports import BudgetRepository
from app.shared.clock import Clock


class DeleteBudget:
    """Elimina el presupuesto (baja lógica). Idempotente: inexistente, ajeno o ya eliminado
    no hace nada. No confirma la transacción."""

    def __init__(self, budgets: BudgetRepository, clock: Clock) -> None:
        self._budgets = budgets
        self._clock = clock

    async def execute(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
        budget = await self._budgets.get(budget_id)
        if budget is None or budget.user_id != user_id or budget.deleted_at is not None:
            return
        await self._budgets.mark_deleted(budget_id, self._clock.now())
