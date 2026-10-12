import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.infrastructure.models import TransactionModel


def _to_entity(row: TransactionModel) -> Transaction:
    return Transaction(
        id=row.id,
        user_id=row.user_id,
        type=row.type,
        amount_minor=row.amount_minor,
        category_id=row.category_id,
        occurred_on=row.occurred_on,
        created_at=row.created_at,
        description=row.description,
        note=row.note,
        tags=list(row.tags),
        status=row.status,
        recurring_rule_id=row.recurring_rule_id,
        deleted_at=row.deleted_at,
    )


class SqlTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, transaction_id: uuid.UUID) -> Transaction | None:
        row = await self._s.get(TransactionModel, transaction_id, populate_existing=True)
        return _to_entity(row) if row else None

    async def add(self, transaction: Transaction) -> None:
        self._s.add(
            TransactionModel(
                id=transaction.id,
                user_id=transaction.user_id,
                type=transaction.type,
                amount_minor=transaction.amount_minor,
                category_id=transaction.category_id,
                occurred_on=transaction.occurred_on,
                created_at=transaction.created_at,
                description=transaction.description,
                note=transaction.note,
                tags=transaction.tags,
                status=transaction.status,
                recurring_rule_id=transaction.recurring_rule_id,
            )
        )
        await self._s.flush()

    async def update(self, transaction: Transaction) -> None:
        await self._s.execute(
            update(TransactionModel)
            .where(
                TransactionModel.id == transaction.id,
                TransactionModel.user_id == transaction.user_id,
            )
            .values(
                amount_minor=transaction.amount_minor,
                category_id=transaction.category_id,
                occurred_on=transaction.occurred_on,
                description=transaction.description,
                note=transaction.note,
                tags=transaction.tags,
                status=transaction.status,
                deleted_at=transaction.deleted_at,
            )
        )

    async def mark_deleted(self, transaction_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(TransactionModel)
            .where(TransactionModel.id == transaction_id)
            .values(deleted_at=at)
        )
