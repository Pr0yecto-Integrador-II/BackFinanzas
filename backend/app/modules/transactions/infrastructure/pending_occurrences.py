import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.infrastructure.models import TransactionModel


class SqlPendingOccurrences:
    """Responde a `recurring` descartando las ocurrencias por confirmar de una regla."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def discard(self, user_id: uuid.UUID, rule_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(TransactionModel)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.recurring_rule_id == rule_id,
                TransactionModel.status == "pending",
                TransactionModel.deleted_at.is_(None),
            )
            .values(deleted_at=at)
        )
