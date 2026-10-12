import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

from app.modules.budgets.application.delete import DeleteBudget
from app.modules.budgets.application.upsert import UpsertBudget, UpsertBudgetInput
from app.modules.budgets.domain.entities import Budget
from tests.unit.auth.fakes import FakeClock
from tests.unit.transactions.fakes import FakeCategoryLookup


class FakeBudgets:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Budget] = {}

    async def get(self, budget_id: uuid.UUID) -> Budget | None:
        return self.items.get(budget_id)

    async def exists_active(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        effective_from: date,
        *,
        other_than: uuid.UUID,
    ) -> bool:
        return any(
            b.user_id == user_id
            and b.category_id == category_id
            and b.effective_from == effective_from
            and b.deleted_at is None
            and b.id != other_than
            for b in self.items.values()
        )

    async def add(self, budget: Budget) -> None:
        self.items[budget.id] = budget

    async def update(self, budget: Budget) -> None:
        self.items[budget.id] = budget

    async def mark_deleted(self, budget_id: uuid.UUID, at: datetime) -> None:
        self.items[budget_id] = replace(self.items[budget_id], deleted_at=at)


class World:
    def __init__(self) -> None:
        self.user = uuid.uuid4()
        self.clock = FakeClock()
        self.repo = FakeBudgets()
        self.categories = FakeCategoryLookup()
        self.expense_cat = self.categories.add(self.user, "expense")
        self.income_cat = self.categories.add(self.user, "income")
        self.upsert = UpsertBudget(self.repo, self.categories)
        self.delete = DeleteBudget(self.repo, self.clock)

    def input(self, **over: object) -> UpsertBudgetInput:
        base: dict[str, object] = {
            "id": uuid.uuid4(),
            "category_id": self.expense_cat,
            "amount_minor": 60_000_000,
            "effective_from": date(2026, 10, 1),
            "created_at": datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
        }
        return UpsertBudgetInput(**{**base, **over})  # type: ignore[arg-type]

    async def create(self, **over: object) -> uuid.UUID:
        data = self.input(**over)
        await self.upsert.execute(self.user, data)
        return data.id
