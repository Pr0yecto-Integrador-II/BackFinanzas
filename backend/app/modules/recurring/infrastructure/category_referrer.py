import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recurring.infrastructure.models import RecurringRuleModel


class RecurringCategoryReferrer:
    """Responde a `categories` sobre el uso de una categoría en reglas recurrentes (HU08)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def is_referenced(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        found = await self._s.scalar(
            select(RecurringRuleModel.id)
            .where(
                RecurringRuleModel.user_id == user_id,
                RecurringRuleModel.category_id == category_id,
                RecurringRuleModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        return found is not None

    async def move(
        self, user_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID, at: datetime
    ) -> None:
        await self._s.execute(
            update(RecurringRuleModel)
            .where(RecurringRuleModel.user_id == user_id, RecurringRuleModel.category_id == from_id)
            .values(category_id=to_id)
        )
