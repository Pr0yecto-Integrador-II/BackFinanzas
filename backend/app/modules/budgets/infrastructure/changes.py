from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budgets.infrastructure.models import BudgetModel
from app.shared.changes import ModelChangesSource


def budget_changes(session: AsyncSession) -> ModelChangesSource:
    return ModelChangesSource(
        session,
        "budget",
        BudgetModel,
        ("category_id", "amount_minor", "effective_from", "created_at"),
    )
