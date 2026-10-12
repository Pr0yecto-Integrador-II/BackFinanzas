import uuid
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Budget:
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    amount_minor: int
    effective_from: date
    created_at: datetime
    deleted_at: datetime | None = None
