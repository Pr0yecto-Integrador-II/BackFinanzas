import uuid
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class Transaction:
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    amount_minor: int
    category_id: uuid.UUID
    occurred_on: date
    created_at: datetime
    description: str | None = None
    note: str | None = None
    tags: list[str] = field(default_factory=list)
    status: str = "confirmed"
    recurring_rule_id: uuid.UUID | None = None
    deleted_at: datetime | None = None
