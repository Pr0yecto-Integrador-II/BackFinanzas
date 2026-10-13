import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: uuid.UUID
    email: str
    password_hash: str
    currency: str


@dataclass(frozen=True)
class RefreshToken:
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    family_id: uuid.UUID
    expires_at: datetime
    revoked_at: datetime | None = None
