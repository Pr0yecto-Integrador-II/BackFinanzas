import uuid
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class RecurringRule:
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    amount_minor: int
    category_id: uuid.UUID
    frequency: str
    start_on: date
    mode: str
    generate_from: date
    created_at: datetime
    description: str | None = None
    end_on: date | None = None
    max_occurrences: int | None = None
    paused_at: datetime | None = None
    deleted_at: datetime | None = None
