"""Adaptadores del push: validan la forma de `data` y llaman al caso de uso del módulo dueño."""

import uuid
from datetime import date
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, ValidationError

from app.modules.budgets.application.delete import DeleteBudget
from app.modules.budgets.application.upsert import UpsertBudget, UpsertBudgetInput
from app.modules.categories.application.delete import DeleteCategory
from app.modules.categories.application.upsert import UpsertCategory, UpsertCategoryInput
from app.modules.recurring.application.delete import DeleteRule
from app.modules.recurring.application.upsert import UpsertRule, UpsertRuleInput
from app.modules.sync.domain.errors import InvalidChangeError
from app.modules.transactions.application.delete import DeleteTransaction
from app.modules.transactions.application.upsert import UpsertTransaction, UpsertTransactionInput


class _Data(BaseModel):
    model_config = ConfigDict(extra="forbid")


_Text = Field(default=None, max_length=2000)  # tope contra abusos; el dominio fija los reales


class CategoryData(_Data):
    name: str = Field(max_length=2000)
    type: str = Field(max_length=20)
    icon: str = Field(max_length=64)
    color: str = Field(max_length=16)
    created_at: AwareDatetime


class TransactionData(_Data):
    type: str = Field(max_length=20)
    amount_minor: StrictInt
    category_id: uuid.UUID
    occurred_on: date
    created_at: AwareDatetime
    description: str | None = _Text
    note: str | None = _Text
    tags: list[str] = Field(default_factory=list, max_length=50)
    status: str = Field(default="confirmed", max_length=20)
    recurring_rule_id: uuid.UUID | None = None


class RuleData(_Data):
    type: str = Field(max_length=20)
    amount_minor: StrictInt
    category_id: uuid.UUID
    frequency: str = Field(max_length=20)
    start_on: date
    mode: str = Field(max_length=20)
    generate_from: date
    created_at: AwareDatetime
    description: str | None = _Text
    end_on: date | None = None
    max_occurrences: StrictInt | None = None
    paused_at: AwareDatetime | None = None


class BudgetData(_Data):
    category_id: uuid.UUID
    amount_minor: StrictInt
    effective_from: date
    created_at: AwareDatetime


class DeleteCategoryData(_Data):
    reassign_to: uuid.UUID | None = None


class NoData(_Data):
    pass


def _has_nul(value: Any) -> bool:
    if isinstance(value, str):
        return "\x00" in value
    if isinstance(value, list):
        return any(_has_nul(v) for v in value)
    return False


def _parse[T: BaseModel](model: type[T], data: dict[str, Any]) -> T:
    try:
        parsed = model.model_validate(data)
        # PostgreSQL no admite el carácter NUL en texto: rechazarlo aquí evita un error de base.
        bad = sorted(name for name, v in parsed.model_dump().items() if _has_nul(v))
        if bad:
            raise InvalidChangeError(f"Datos inválidos en: {', '.join(bad)}.")
        return parsed
    except ValidationError as exc:
        fields = ", ".join(
            sorted({".".join(str(p) for p in e["loc"]) or "data" for e in exc.errors()})
        )
        raise InvalidChangeError(f"Datos inválidos en: {fields}.") from exc


class CategoryHandler:
    def __init__(self, upsert: UpsertCategory, delete: DeleteCategory) -> None:
        self._upsert, self._delete = upsert, delete

    async def upsert(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        d = _parse(CategoryData, data)
        await self._upsert.execute(
            user_id, UpsertCategoryInput(change_id, d.name, d.type, d.icon, d.color, d.created_at)
        )

    async def delete(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        d = _parse(DeleteCategoryData, data)
        await self._delete.execute(user_id, change_id, d.reassign_to)


class TransactionHandler:
    def __init__(self, upsert: UpsertTransaction, delete: DeleteTransaction) -> None:
        self._upsert, self._delete = upsert, delete

    async def upsert(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        d = _parse(TransactionData, data)
        await self._upsert.execute(user_id, UpsertTransactionInput(id=change_id, **d.model_dump()))

    async def delete(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        _parse(NoData, data)
        await self._delete.execute(user_id, change_id)


class RuleHandler:
    def __init__(self, upsert: UpsertRule, delete: DeleteRule) -> None:
        self._upsert, self._delete = upsert, delete

    async def upsert(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        d = _parse(RuleData, data)
        await self._upsert.execute(user_id, UpsertRuleInput(id=change_id, **d.model_dump()))

    async def delete(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        _parse(NoData, data)
        await self._delete.execute(user_id, change_id)


class BudgetHandler:
    def __init__(self, upsert: UpsertBudget, delete: DeleteBudget) -> None:
        self._upsert, self._delete = upsert, delete

    async def upsert(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        d = _parse(BudgetData, data)
        await self._upsert.execute(user_id, UpsertBudgetInput(id=change_id, **d.model_dump()))

    async def delete(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        _parse(NoData, data)
        await self._delete.execute(user_id, change_id)
