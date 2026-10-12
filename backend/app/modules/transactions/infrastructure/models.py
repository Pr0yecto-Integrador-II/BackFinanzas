import uuid
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Text

from app.shared.db import Base, SyncColumns


class TransactionModel(SyncColumns, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('expense', 'income')", name="type"),
        CheckConstraint("amount_minor > 0 AND amount_minor <= 999999999999999", name="amount"),
        CheckConstraint("cardinality(tags) <= 5", name="tags_max"),
        CheckConstraint("status IN ('confirmed', 'pending')", name="status"),
        Index(
            "ix_transactions_user_occurred",
            "user_id",
            text("occurred_on DESC"),
            text("created_at DESC"),
        ),
        Index("ix_transactions_user_version", "user_id", "version"),
        Index("ix_transactions_recurring_rule_id", "recurring_rule_id"),
        Index("ix_transactions_tags", "tags", postgresql_using="gin"),
    )

    type: Mapped[str] = mapped_column(String(7), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    status: Mapped[str] = mapped_column(String(9), nullable=False, server_default="confirmed")
    recurring_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurring_rules.id")
    )
