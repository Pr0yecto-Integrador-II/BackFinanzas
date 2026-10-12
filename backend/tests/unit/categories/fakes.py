import uuid
from dataclasses import replace
from datetime import UTC, datetime

from app.modules.categories.application.create_defaults import CreateDefaultCategories
from app.modules.categories.application.delete import DeleteCategory
from app.modules.categories.application.upsert import UpsertCategory, UpsertCategoryInput
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.errors import CategoryNameTakenError
from tests.unit.auth.fakes import FakeClock


class FakeCategories:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Category] = {}
        self.locked: list[uuid.UUID] = []

    async def lock_user_categories(self, user_id: uuid.UUID) -> None:
        self.locked.append(user_id)

    async def get(self, category_id: uuid.UUID) -> Category | None:
        return self.items.get(category_id)

    async def add(self, category: Category) -> None:
        if await self.name_taken(category.user_id, category.type, category.name_key, None):
            raise CategoryNameTakenError(category.type)
        self.items[category.id] = category

    async def update(self, category: Category) -> None:
        self.items[category.id] = category

    async def name_taken(
        self, user_id: uuid.UUID, type_: str, name_key: str, exclude_id: uuid.UUID | None
    ) -> bool:
        return any(
            c.user_id == user_id
            and c.type == type_
            and c.name_key == name_key
            and c.deleted_at is None
            and c.id != exclude_id
            for c in self.items.values()
        )

    async def count_active(self, user_id: uuid.UUID, type_: str) -> int:
        return sum(
            1
            for c in self.items.values()
            if c.user_id == user_id and c.type == type_ and c.deleted_at is None
        )

    async def mark_deleted(self, category_id: uuid.UUID, at: datetime) -> None:
        self.items[category_id] = replace(self.items[category_id], deleted_at=at)


class FakeReferrer:
    """Simula a un módulo (movimientos, reglas o presupuestos) que usa categorías."""

    def __init__(self) -> None:
        self.used: set[uuid.UUID] = set()
        self.moves: list[tuple[uuid.UUID, uuid.UUID]] = []

    async def is_referenced(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        return category_id in self.used

    async def move(
        self, user_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID, at: datetime
    ) -> None:
        self.moves.append((from_id, to_id))
        if from_id in self.used:
            self.used.discard(from_id)
            self.used.add(to_id)


class World:
    def __init__(self) -> None:
        self.user = uuid.uuid4()
        self.clock = FakeClock()
        self.repo = FakeCategories()
        self.tx, self.rules, self.budgets = FakeReferrer(), FakeReferrer(), FakeReferrer()
        referrers = [self.tx, self.rules, self.budgets]
        self.defaults = CreateDefaultCategories(self.repo, self.clock)
        self.upsert = UpsertCategory(self.repo, referrers)  # type: ignore[arg-type]
        self.delete = DeleteCategory(self.repo, referrers, self.clock)  # type: ignore[arg-type]

    async def create(
        self, name: str, type_: str = "expense", user: uuid.UUID | None = None
    ) -> uuid.UUID:
        cid = uuid.uuid4()
        await self.upsert.execute(user or self.user, self.input(cid, name, type_))
        return cid

    @staticmethod
    def input(
        cid: uuid.UUID, name: str, type_: str = "expense", **over: str
    ) -> UpsertCategoryInput:
        fields = {"icon": "pets", "color": "#F97316", **over}
        return UpsertCategoryInput(
            cid, name, type_, fields["icon"], fields["color"], datetime(2026, 10, 1, tzinfo=UTC)
        )

    def by_name(self, name: str, type_: str = "expense") -> Category:
        return next(
            c
            for c in self.repo.items.values()
            if c.name == name and c.type == type_ and c.deleted_at is None
        )
