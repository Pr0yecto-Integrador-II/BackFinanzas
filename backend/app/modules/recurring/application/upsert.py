import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime

from app.modules.recurring.application.ports import CategoryLookup, RecurringRuleRepository
from app.modules.recurring.domain.entities import RecurringRule
from app.modules.recurring.domain.errors import (
    CategoryTypeMismatchError,
    InvalidCategoryError,
    RuleNotFoundError,
)
from app.modules.recurring.domain.rules import (
    clean_description,
    validate_amount,
    validate_end,
    validate_frequency,
    validate_generate_from,
    validate_mode,
    validate_type,
)


@dataclass(frozen=True)
class UpsertRuleInput:
    id: uuid.UUID
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
    paused_at: datetime | None = None  # con valor = pausada; nulo = activa


class UpsertRule:
    """Valida y guarda una regla recurrente (HU09). La ejecución ocurre en el navegador.

    Editar la regla no toca los movimientos ya generados (regla 6): solo guarda la plantilla.
    No confirma la transacción: quien la llama (la sincronización) decide cuándo.
    """

    def __init__(self, rules: RecurringRuleRepository, categories: CategoryLookup) -> None:
        self._rules = rules
        self._categories = categories

    async def execute(self, user_id: uuid.UUID, data: UpsertRuleInput) -> None:
        existing = await self._rules.get(data.id)
        # Ajena o eliminada: se trata como inexistente (no se revela, y no hay "deshacer").
        if existing is not None and (existing.user_id != user_id or existing.deleted_at):
            raise RuleNotFoundError

        type_ = validate_type(data.type)
        amount = validate_amount(data.amount_minor)
        description = clean_description(data.description)
        frequency = validate_frequency(data.frequency)
        mode = validate_mode(data.mode)
        validate_end(data.start_on, data.end_on, data.max_occurrences)
        validate_generate_from(
            data.start_on, data.generate_from, existing.generate_from if existing else None
        )

        category_type = await self._categories.active_type(user_id, data.category_id)
        if category_type is None:
            raise InvalidCategoryError
        if category_type != type_:
            raise CategoryTypeMismatchError(type_)

        fields = {
            "type": type_,
            "amount_minor": amount,
            "category_id": data.category_id,
            "description": description,
            "frequency": frequency,
            "start_on": data.start_on,
            "end_on": data.end_on,
            "max_occurrences": data.max_occurrences,
            "mode": mode,
            "generate_from": data.generate_from,
            "paused_at": data.paused_at,
        }
        if existing is None:
            await self._rules.add(
                RecurringRule(id=data.id, user_id=user_id, created_at=data.created_at, **fields)  # type: ignore[arg-type]
            )
        else:
            await self._rules.update(replace(existing, **fields))  # type: ignore[arg-type]
