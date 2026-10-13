import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, SyncColumns


class RecurringRuleModel(SyncColumns, Base):
    __tablename__ = "recurring_rules"
    __table_args__ = (
        CheckConstraint("type IN ('expense', 'income')", name="type"),
        CheckConstraint("amount_minor > 0 AND amount_minor <= 999999999999999", name="amount"),
        CheckConstraint(
            "frequency IN ('daily', 'weekly', 'biweekly', 'monthly', 'yearly')", name="frequency"
        ),
        CheckConstraint("mode IN ('auto', 'confirm')", name="mode"),
        CheckConstraint("max_occurrences > 0", name="max_occurrences"),
        CheckConstraint("end_on IS NULL OR max_occurrences IS NULL", name="single_end"),
        Index("ix_recurring_rules_user_version", "user_id", "version"),
    )

    type: Mapped[str] = mapped_column(String(7), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(100))
    frequency: Mapped[str] = mapped_column(String(9), nullable=False)
    start_on: Mapped[date] = mapped_column(Date, nullable=False)
    end_on: Mapped[date | None] = mapped_column(Date)
    max_occurrences: Mapped[int | None] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(7), nullable=False)
    generate_from: Mapped[date] = mapped_column(Date, nullable=False)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
