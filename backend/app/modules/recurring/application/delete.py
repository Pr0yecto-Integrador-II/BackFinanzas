import uuid

from app.modules.recurring.application.ports import PendingOccurrences, RecurringRuleRepository
from app.shared.clock import Clock


class DeleteRule:
    """Elimina la regla (HU09 regla 8): deja de generar, conserva lo ya registrado y descarta
    las ocurrencias que seguían por confirmar.

    Es idempotente: inexistente, ajena o ya eliminada no hace nada. No confirma la transacción.
    """

    def __init__(
        self, rules: RecurringRuleRepository, pending: PendingOccurrences, clock: Clock
    ) -> None:
        self._rules = rules
        self._pending = pending
        self._clock = clock

    async def execute(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> None:
        rule = await self._rules.get(rule_id)
        if rule is None or rule.user_id != user_id or rule.deleted_at is not None:
            return
        now = self._clock.now()
        await self._pending.discard(user_id, rule_id, now)
        await self._rules.mark_deleted(rule_id, now)
