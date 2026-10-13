import uuid

from app.modules.categories.application.create_defaults import CreateDefaultCategories


class CategoriesSeeder:
    """Adapta el puerto de `auth` al caso de uso de `categories` (D-15)."""

    def __init__(self, create_defaults: CreateDefaultCategories) -> None:
        self._create_defaults = create_defaults

    async def seed(self, user_id: uuid.UUID) -> None:
        await self._create_defaults.execute(user_id)
