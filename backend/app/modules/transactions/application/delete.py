import uuid

from app.modules.transactions.application.ports import TransactionRepository
from app.shared.clock import Clock


class DeleteTransaction:
    """Eliminación lógica (HU07). Idempotente: inexistente, ajeno o ya eliminado no hace nada.

    No confirma la transacción. Borrar una ocurrencia recurrente no afecta a su regla.
    """

    def __init__(self, transactions: TransactionRepository, clock: Clock) -> None:
        self._transactions = transactions
        self._clock = clock

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
        tx = await self._transactions.get(transaction_id)
        if tx is None or tx.user_id != user_id or tx.deleted_at is not None:
            return
        await self._transactions.mark_deleted(transaction_id, self._clock.now())
