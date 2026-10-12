import uuid

from app.modules.categories.application.ports import CategoryRepository
from app.modules.categories.domain.catalog import DEFAULT_CATEGORIES
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.rules import name_key
from app.shared.clock import Clock


class CreateDefaultCategories:
    """Crea las 12 categorías de HU01. No confirma: forma parte de la transacción del registro."""

    def __init__(self, categories: CategoryRepository, clock: Clock) -> None:
        self._categories = categories
        self._clock = clock

    async def execute(self, user_id: uuid.UUID) -> None:
        now = self._clock.now()
        for name, type_, icon, color in DEFAULT_CATEGORIES:
            await self._categories.add(
                Category(uuid.uuid4(), user_id, name, name_key(name), type_, icon, color, True, now)
            )
