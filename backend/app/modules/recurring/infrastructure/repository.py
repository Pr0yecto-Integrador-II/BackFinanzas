import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recurring.domain.entities import RecurringRule
from app.modules.recurring.infrastructure.models import RecurringRuleModel


def _to_entity(row: RecurringRuleModel) -> RecurringRule:
    return RecurringRule(
        id=row.id,
        user_id=row.user_id,
        type=row.type,
        amount_minor=row.amount_minor,
        category_id=row.category_id,
        frequency=row.frequency,
        start_on=row.start_on,
        mode=row.mode,
        generate_from=row.generate_from,
        created_at=row.created_at,
        description=row.description,
        end_on=row.end_on,
        max_occurrences=row.max_occurrences,
        paused_at=row.paused_at,
        deleted_at=row.deleted_at,
    )


_EDITABLE = (
    "type",
    "amount_minor",
    "category_id",
    "description",
    "frequency",
    "start_on",
    "end_on",
    "max_occurrences",
    "mode",
    "generate_from",
    "paused_at",
)


class SqlRecurringRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, rule_id: uuid.UUID) -> RecurringRule | None:
        row = await self._s.get(RecurringRuleModel, rule_id, populate_existing=True)
        return _to_entity(row) if row else None

    async def add(self, rule: RecurringRule) -> None:
        values = {name: getattr(rule, name) for name in _EDITABLE}
        self._s.add(
            RecurringRuleModel(
                id=rule.id, user_id=rule.user_id, created_at=rule.created_at, **values
            )
        )
        await self._s.flush()

    async def update(self, rule: RecurringRule) -> None:
        values = {name: getattr(rule, name) for name in _EDITABLE}
        await self._s.execute(
            update(RecurringRuleModel)
            .where(RecurringRuleModel.id == rule.id, RecurringRuleModel.user_id == rule.user_id)
            .values(**values)
        )

    async def mark_deleted(self, rule_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(RecurringRuleModel).where(RecurringRuleModel.id == rule_id).values(deleted_at=at)
        )
