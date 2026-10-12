import uuid
from dataclasses import dataclass, replace
from datetime import datetime

from app.modules.categories.application.ports import CategoryReferrer, CategoryRepository
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.errors import (
    CategoryNameTakenError,
    CategoryNotFoundError,
    CategoryTypeLockedError,
)
from app.modules.categories.domain.rules import (
    clean_name,
    name_key,
    validate_color,
    validate_icon,
    validate_type,
)


@dataclass(frozen=True)
class UpsertCategoryInput:
    id: uuid.UUID
    name: str
    type: str
    icon: str
    color: str
    created_at: datetime  # momento en que se creó en el dispositivo (Blueprint 6.3.2)


class UpsertCategory:
    """Crea o edita una categoría con el `id` que generó el cliente (HU08).

    No confirma la transacción: quien la llama (la sincronización) decide cuándo.
    """

    def __init__(self, categories: CategoryRepository, referrers: list[CategoryReferrer]) -> None:
        self._categories = categories
        self._referrers = referrers

    async def execute(self, user_id: uuid.UUID, data: UpsertCategoryInput) -> None:
        name = clean_name(data.name)
        key = name_key(name)
        type_ = validate_type(data.type)
        icon = validate_icon(data.icon)
        color = validate_color(data.color)

        existing = await self._categories.get(data.id)
        # Una categoría ajena se trata igual que una inexistente: no se revela que existe.
        if existing is not None and (existing.user_id != user_id or existing.deleted_at):
            raise CategoryNotFoundError

        if await self._categories.name_taken(user_id, type_, key, exclude_id=data.id):
            raise CategoryNameTakenError(type_)

        if existing is None:
            await self._categories.add(
                Category(data.id, user_id, name, key, type_, icon, color, False, data.created_at)
            )
            return

        if existing.type != type_ and await self._is_in_use(user_id, existing.id):
            raise CategoryTypeLockedError
        await self._categories.update(
            replace(existing, name=name, name_key=key, type=type_, icon=icon, color=color)
        )

    async def _is_in_use(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        for referrer in self._referrers:
            if await referrer.is_referenced(user_id, category_id):
                return True
        return False
