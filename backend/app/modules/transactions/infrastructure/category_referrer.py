import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.infrastructure.models import TransactionModel


class TransactionCategoryReferrer:
    """Responde a `categories` sobre el uso de una categoría en movimientos (HU08)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def is_referenced(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        found = await self._s.scalar(
            select(TransactionModel.id)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.category_id == category_id,
                TransactionModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        return found is not None

    async def move(
        self, user_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID, at: datetime
    ) -> None:
        # Incluye los borrados lógicos, para que ninguna fila apunte a la categoría eliminada.
        # El trigger de la base sube la `version` de cada fila y así llega a los otros dispositivos.
        await self._s.execute(
            update(TransactionModel)
            .where(TransactionModel.user_id == user_id, TransactionModel.category_id == from_id)
            .values(category_id=to_id)
        )
