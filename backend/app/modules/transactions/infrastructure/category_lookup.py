import uuid

from app.modules.categories.application.get_active import GetActiveCategory


class CategoriesLookup:
    """Adapta la consulta que ofrece `categories` al puerto de `transactions`."""

    def __init__(self, get_active: GetActiveCategory) -> None:
        self._get_active = get_active

    async def active_type(self, user_id: uuid.UUID, category_id: uuid.UUID) -> str | None:
        category = await self._get_active.execute(user_id, category_id)
        return category.type if category else None
