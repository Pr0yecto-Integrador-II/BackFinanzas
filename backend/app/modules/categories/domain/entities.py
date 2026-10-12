import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Category:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    name_key: str
    type: str
    icon: str
    color: str
    is_default: bool
    created_at: datetime
    deleted_at: datetime | None = None
