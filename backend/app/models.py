"""Importa todos los modelos para que Alembic los vea en `Base.metadata`."""

from app.modules.auth.infrastructure import models as _auth
from app.modules.budgets.infrastructure import models as _budgets
from app.modules.categories.infrastructure import models as _categories
from app.modules.recurring.infrastructure import models as _recurring
from app.modules.transactions.infrastructure import models as _transactions
from app.shared.db import Base

__all__ = ["Base", "_auth", "_budgets", "_categories", "_recurring", "_transactions"]
