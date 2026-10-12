from sqlalchemy import CHAR, Boolean, CheckConstraint, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, SyncColumns


class CategoryModel(SyncColumns, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("type IN ('expense', 'income')", name="type"),
        Index(
            "uq_categories_user_type_name_key",
            "user_id",
            "type",
            "name_key",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_categories_user_version", "user_id", "version"),
    )

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    name_key: Mapped[str] = mapped_column(String(30), nullable=False)
    type: Mapped[str] = mapped_column(String(7), nullable=False)
    icon: Mapped[str] = mapped_column(String(32), nullable=False)
    color: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
