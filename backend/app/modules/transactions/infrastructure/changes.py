from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.infrastructure.models import TransactionModel
from app.shared.changes import ModelChangesSource


def transaction_changes(session: AsyncSession) -> ModelChangesSource:
    return ModelChangesSource(
        session,
        "transaction",
        TransactionModel,
        (
            "type", "amount_minor", "category_id", "occurred_on", "description", "note",
            "tags", "status", "recurring_rule_id", "created_at",
        ),
    )  # fmt: skip
