import uuid
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, SyncColumns


class BudgetModel(SyncColumns, Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="amount"),
        CheckConstraint("EXTRACT(DAY FROM effective_from) = 1", name="first_of_month"),
        Index(
            "uq_budgets_user_category_effective",
            "user_id",
            "category_id",
            "effective_from",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_budgets_user_version", "user_id", "version"),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
