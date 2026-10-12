import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_VERSION = 2**63 - 1  # tope de BIGINT: más allá, la base daría error
MAX_CHANGES = 500  # D-12: acota la transacción y el bloqueo por usuario


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChangeIn(_In):
    entity: Literal["category", "recurring_rule", "transaction", "budget"]
    op: Literal["upsert", "delete"]
    id: uuid.UUID
    data: dict[str, Any] = Field(default_factory=dict)


class PushIn(_In):
    changes: list[ChangeIn] = Field(max_length=MAX_CHANGES)


class RejectedOut(BaseModel):
    id: uuid.UUID
    code: str
    message: str


class PushOut(BaseModel):
    applied: list[uuid.UUID]
    rejected: list[RejectedOut]
    version: int


class PullChangeOut(BaseModel):
    entity: str
    id: uuid.UUID
    version: int
    data: dict[str, Any]
    deleted: bool


class PullOut(BaseModel):
    changes: list[PullChangeOut]
    next_since: int
    has_more: bool
