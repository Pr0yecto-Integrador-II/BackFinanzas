import uuid
from datetime import datetime
from typing import Protocol

from app.modules.categories.domain.entities import Category


class CategoryRepository(Protocol):
    async def lock_user_categories(self, user_id: uuid.UUID) -> None:
        """Serializa las operaciones concurrentes sobre las categorías de un usuario."""

    async def get(self, category_id: uuid.UUID) -> Category | None:
        """Busca por id sin filtrar por usuario; el caso de uso decide si es del usuario."""

    async def add(self, category: Category) -> None:
        """Lanza CategoryNameTakenError si otra categoría activa tiene el mismo nombre y tipo."""

    async def update(self, category: Category) -> None: ...

    async def name_taken(
        self, user_id: uuid.UUID, type_: str, name_key: str, exclude_id: uuid.UUID | None
    ) -> bool: ...

    async def count_active(self, user_id: uuid.UUID, type_: str) -> int: ...

    async def mark_deleted(self, category_id: uuid.UUID, at: datetime) -> None: ...


class CategoryReferrer(Protocol):
    """Lo implementa cada módulo que guarda `category_id` (movimientos, reglas, presupuestos).

    Así `categories` nunca toca las tablas de otros módulos.
    """

    async def is_referenced(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool: ...

    async def move(
        self, user_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID, at: datetime
    ) -> None: ...
