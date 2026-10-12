import uuid

from app.modules.categories.application.ports import CategoryRepository
from app.modules.categories.domain.entities import Category


class GetActiveCategory:
    """Consulta que `categories` ofrece a otros módulos: la categoría activa del usuario."""

    def __init__(self, categories: CategoryRepository) -> None:
        self._categories = categories

    async def execute(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Category | None:
        category = await self._categories.get(category_id)
        if category is None or category.user_id != user_id or category.deleted_at is not None:
            return None  # ajena o eliminada: se trata igual que inexistente
        return category
