import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

from app.modules.transactions.application.delete import DeleteTransaction
from app.modules.transactions.application.upsert import UpsertTransaction, UpsertTransactionInput
from app.modules.transactions.domain.entities import Transaction
from tests.unit.auth.fakes import FakeClock


class FakeTransactions:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Transaction] = {}

    async def get(self, transaction_id: uuid.UUID) -> Transaction | None:
        return self.items.get(transaction_id)

    async def add(self, transaction: Transaction) -> None:
        self.items[transaction.id] = transaction

    async def update(self, transaction: Transaction) -> None:
        self.items[transaction.id] = transaction

    async def mark_deleted(self, transaction_id: uuid.UUID, at: datetime) -> None:
        self.items[transaction_id] = replace(self.items[transaction_id], deleted_at=at)


class FakeCategoryLookup:
    def __init__(self) -> None:
        self.categories: dict[tuple[uuid.UUID, uuid.UUID], str] = {}

    def add(self, user: uuid.UUID, type_: str) -> uuid.UUID:
        cid = uuid.uuid4()
        self.categories[(user, cid)] = type_
        return cid

    async def active_type(self, user_id: uuid.UUID, category_id: uuid.UUID) -> str | None:
        return self.categories.get((user_id, category_id))


class FakeRuleLookup:
    def __init__(self) -> None:
        self.rules: dict[tuple[uuid.UUID, uuid.UUID], str] = {}

    async def state(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> str | None:
        return self.rules.get((user_id, rule_id))


class World:
    def __init__(self) -> None:
        self.user = uuid.uuid4()
        self.clock = FakeClock()  # 2026-10-12
        self.repo = FakeTransactions()
        self.categories = FakeCategoryLookup()
        self.rules = FakeRuleLookup()
        self.expense_cat = self.categories.add(self.user, "expense")
        self.income_cat = self.categories.add(self.user, "income")
        self.upsert = UpsertTransaction(self.repo, self.categories, self.rules, self.clock)
        self.delete = DeleteTransaction(self.repo, self.clock)

    def input(self, **over: object) -> UpsertTransactionInput:
        base: dict[str, object] = {
            "id": uuid.uuid4(),
            "type": "expense",
            "amount_minor": 2_500_000,
            "category_id": self.expense_cat,
            "occurred_on": date(2026, 10, 12),
            "created_at": datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        }
        return UpsertTransactionInput(**{**base, **over})  # type: ignore[arg-type]

    async def create(self, **over: object) -> uuid.UUID:
        data = self.input(**over)
        await self.upsert.execute(self.user, data)
        return data.id

    def rule(self) -> uuid.UUID:
        rid = uuid.uuid4()
        self.rules.rules[(self.user, rid)] = "active"
        return rid
