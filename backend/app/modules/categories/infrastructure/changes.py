from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.infrastructure.models import CategoryModel
from app.shared.changes import ModelChangesSource


def category_changes(session: AsyncSession) -> ModelChangesSource:
    return ModelChangesSource(
        session,
        "category",
        CategoryModel,
        ("name", "type", "icon", "color", "is_default", "created_at"),
    )
