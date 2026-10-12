import uuid
from datetime import UTC, date, datetime

import pytest_asyncio

from app import composition
from app.modules.recurring.application.upsert import UpsertRuleInput
from tests.integration.conftest import Db
from tests.integration.transactions.conftest import TxApi


class RuleApi:
    def __init__(self, db: Db) -> None:
        self.db = db
        self.upsert = composition.upsert_rule(db.s)
        self.delete = composition.delete_rule(db.s, db.clock)
        self.tx = TxApi(db)

    @staticmethod
    def input(category: uuid.UUID, **over: object) -> UpsertRuleInput:
        base: dict[str, object] = {
            "id": uuid.uuid4(),
            "type": "expense",
            "amount_minor": 120_000_000,
            "category_id": category,
            "frequency": "monthly",
            "start_on": date(2026, 10, 5),
            "mode": "confirm",
            "generate_from": date(2026, 10, 5),
            "created_at": datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
        }
        return UpsertRuleInput(**{**base, **over})  # type: ignore[arg-type]


@pytest_asyncio.fixture
async def rules(db: Db) -> RuleApi:
    return RuleApi(db)
