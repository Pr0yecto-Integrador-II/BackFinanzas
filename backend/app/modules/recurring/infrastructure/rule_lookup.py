import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recurring.infrastructure.models import RecurringRuleModel


class SqlRecurringRuleLookup:
    """Dice a `transactions` en qué estado está una regla del usuario.

    Una regla eliminada sigue existiendo: sus movimientos ya registrados conservan el enlace.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def state(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> str | None:
        row = (
            await self._s.execute(
                select(RecurringRuleModel.deleted_at).where(
                    RecurringRuleModel.id == rule_id, RecurringRuleModel.user_id == user_id
                )
            )
        ).first()
        if row is None:
            return None
        return "deleted" if row[0] is not None else "active"
