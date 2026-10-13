import uuid
from datetime import UTC, date, datetime

import pytest_asyncio

from app import composition
from app.modules.transactions.application.upsert import UpsertTransactionInput
from tests.integration.conftest import Db


class TxApi:
    """Los casos de uso de movimientos ya conectados a la base real."""

    def __init__(self, db: Db) -> None:
        self.db = db
        self.upsert = composition.upsert_transaction(db.s, db.clock)
        self.delete = composition.delete_transaction(db.s, db.clock)

    @staticmethod
    def input(category: uuid.UUID, **over: object) -> UpsertTransactionInput:
        base: dict[str, object] = {
            "id": uuid.uuid4(),
            "type": "expense",
            "amount_minor": 2_500_000,
            "category_id": category,
            "occurred_on": date(2026, 10, 12),
            "created_at": datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        }
        return UpsertTransactionInput(**{**base, **over})  # type: ignore[arg-type]


@pytest_asyncio.fixture
async def api(db: Db) -> TxApi:
    return TxApi(db)
