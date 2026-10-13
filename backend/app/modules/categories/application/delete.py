import uuid

from app.modules.categories.application.ports import CategoryReferrer, CategoryRepository
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.errors import (
    InvalidReassignmentError,
    LastCategoryOfTypeError,
    ReassignmentRequiredError,
)
from app.shared.clock import Clock


class DeleteCategory:
    """Elimina (lógicamente) una categoría, reasignando lo que la use a otra (HU08 reglas 5 y 6).

    Es idempotente: eliminar una categoría inexistente, ajena o ya eliminada no hace nada,
    de modo que reenviar el mismo cambio al sincronizar no falla. No confirma la transacción.
    """

    def __init__(
        self, categories: CategoryRepository, referrers: list[CategoryReferrer], clock: Clock
    ) -> None:
        self._categories = categories
        self._referrers = referrers
        self._clock = clock

    async def execute(
        self, user_id: uuid.UUID, category_id: uuid.UUID, reassign_to: uuid.UUID | None = None
    ) -> None:
        await self._categories.lock_user_categories(user_id)
        category = await self._categories.get(category_id)
        if category is None or category.user_id != user_id or category.deleted_at is not None:
            return

        if await self._categories.count_active(user_id, category.type) <= 1:
            raise LastCategoryOfTypeError(category.type)

        now = self._clock.now()
        if await self._is_in_use(user_id, category_id):
            target = await self._valid_target(user_id, category, reassign_to)
            for referrer in self._referrers:
                await referrer.move(user_id, category_id, target.id, now)
        await self._categories.mark_deleted(category_id, now)

    async def _is_in_use(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        for referrer in self._referrers:
            if await referrer.is_referenced(user_id, category_id):
                return True
        return False

    async def _valid_target(
        self, user_id: uuid.UUID, source: Category, reassign_to: uuid.UUID | None
    ) -> Category:
        if reassign_to is None:
            raise ReassignmentRequiredError
        target = await self._categories.get(reassign_to)
        if (
            target is None
            or target.user_id != user_id
            or target.deleted_at is not None
            or target.id == source.id
            or target.type != source.type
        ):
            raise InvalidReassignmentError
        return target
