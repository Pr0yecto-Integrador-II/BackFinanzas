import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.errors import CategoryNameTakenError
from app.modules.categories.infrastructure.models import CategoryModel


def _to_entity(row: CategoryModel) -> Category:
    return Category(
        row.id,
        row.user_id,
        row.name,
        row.name_key,
        row.type,
        row.icon,
        row.color,
        row.is_default,
        row.created_at,
        row.deleted_at,
    )


class SqlCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def lock_user_categories(self, user_id: uuid.UUID) -> None:
        await self._s.execute(
            select(CategoryModel.id).where(CategoryModel.user_id == user_id).with_for_update()
        )

    async def get(self, category_id: uuid.UUID) -> Category | None:
        row = await self._s.get(CategoryModel, category_id, populate_existing=True)
        return _to_entity(row) if row else None

    async def add(self, category: Category) -> None:
        self._s.add(
            CategoryModel(
                id=category.id,
                user_id=category.user_id,
                name=category.name,
                name_key=category.name_key,
                type=category.type,
                icon=category.icon,
                color=category.color,
                is_default=category.is_default,
                created_at=category.created_at,
            )
        )
        await self._flush_mapping_name_conflict(category.type)

    async def update(self, category: Category) -> None:
        await self._s.execute(
            update(CategoryModel)
            .where(CategoryModel.id == category.id, CategoryModel.user_id == category.user_id)
            .values(
                name=category.name,
                name_key=category.name_key,
                type=category.type,
                icon=category.icon,
                color=category.color,
            )
        )
        await self._flush_mapping_name_conflict(category.type)

    async def _flush_mapping_name_conflict(self, type_: str) -> None:
        try:
            await self._s.flush()
        except IntegrityError:  # el índice único parcial atrapó una carrera
            raise CategoryNameTakenError(type_) from None

    async def name_taken(
        self, user_id: uuid.UUID, type_: str, name_key: str, exclude_id: uuid.UUID | None
    ) -> bool:
        query = select(CategoryModel.id).where(
            CategoryModel.user_id == user_id,
            CategoryModel.type == type_,
            CategoryModel.name_key == name_key,
            CategoryModel.deleted_at.is_(None),
        )
        if exclude_id is not None:
            query = query.where(CategoryModel.id != exclude_id)
        return (await self._s.scalar(query.limit(1))) is not None

    async def count_active(self, user_id: uuid.UUID, type_: str) -> int:
        return int(
            await self._s.scalar(
                select(func.count()).where(
                    CategoryModel.user_id == user_id,
                    CategoryModel.type == type_,
                    CategoryModel.deleted_at.is_(None),
                )
            )
            or 0
        )

    async def mark_deleted(self, category_id: uuid.UUID, at: datetime) -> None:
        await self._s.execute(
            update(CategoryModel).where(CategoryModel.id == category_id).values(deleted_at=at)
        )
