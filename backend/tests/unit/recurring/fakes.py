import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

from app.modules.recurring.application.delete import DeleteRule
from app.modules.recurring.application.upsert import UpsertRule, UpsertRuleInput
from app.modules.recurring.domain.entities import RecurringRule
from tests.unit.auth.fakes import FakeClock
from tests.unit.transactions.fakes import FakeCategoryLookup


class FakeRules:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, RecurringRule] = {}

    async def get(self, rule_id: uuid.UUID) -> RecurringRule | None:
        return self.items.get(rule_id)

    async def add(self, rule: RecurringRule) -> None:
        self.items[rule.id] = rule

    async def update(self, rule: RecurringRule) -> None:
        self.items[rule.id] = rule

    async def mark_deleted(self, rule_id: uuid.UUID, at: datetime) -> None:
        self.items[rule_id] = replace(self.items[rule_id], deleted_at=at)


class FakePending:
    def __init__(self) -> None:
        self.discarded: list[tuple[uuid.UUID, uuid.UUID, datetime]] = []

    async def discard(self, user_id: uuid.UUID, rule_id: uuid.UUID, at: datetime) -> None:
        self.discarded.append((user_id, rule_id, at))


class World:
    def __init__(self) -> None:
        self.user = uuid.uuid4()
        self.clock = FakeClock()
        self.repo = FakeRules()
        self.categories = FakeCategoryLookup()
        self.pending = FakePending()
        self.expense_cat = self.categories.add(self.user, "expense")
        self.income_cat = self.categories.add(self.user, "income")
        self.upsert = UpsertRule(self.repo, self.categories)
        self.delete = DeleteRule(self.repo, self.pending, self.clock)

    def input(self, **over: object) -> UpsertRuleInput:
        base: dict[str, object] = {
            "id": uuid.uuid4(),
            "type": "expense",
            "amount_minor": 120_000_000,
            "category_id": self.expense_cat,
            "frequency": "monthly",
            "start_on": date(2026, 10, 5),
            "mode": "auto",
            "generate_from": date(2026, 10, 5),
            "created_at": datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
        }
        return UpsertRuleInput(**{**base, **over})  # type: ignore[arg-type]

    async def create(self, **over: object) -> uuid.UUID:
        data = self.input(**over)
        await self.upsert.execute(self.user, data)
        return data.id
