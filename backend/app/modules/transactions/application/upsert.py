import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime

from app.modules.transactions.application.ports import (
    CategoryLookup,
    RecurringRuleLookup,
    TransactionRepository,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.errors import (
    CategoryTypeMismatchError,
    InvalidCategoryError,
    InvalidRecurringRuleError,
    OccurrenceDeletedError,
    PendingWithoutRuleError,
    RecurrenceLinkLockedError,
    RuleDeletedError,
    TransactionNotFoundError,
    TransactionTypeLockedError,
)
from app.modules.transactions.domain.rules import (
    PENDING,
    clean_description,
    clean_note,
    normalize_tags,
    validate_amount,
    validate_date,
    validate_status,
    validate_type,
)
from app.shared.clock import Clock


@dataclass(frozen=True)
class UpsertTransactionInput:
    id: uuid.UUID
    type: str
    amount_minor: int
    category_id: uuid.UUID
    occurred_on: date
    created_at: datetime  # momento de creación en el dispositivo (ordena el día, HU11)
    description: str | None = None
    note: str | None = None
    tags: list[str] = field(default_factory=list)
    status: str = "confirmed"
    recurring_rule_id: uuid.UUID | None = None


class UpsertTransaction:
    """Crea o edita un movimiento con el `id` que generó el cliente (HU04–HU07, HU10).

    No confirma la transacción: quien la llama (la sincronización) decide cuándo.
    """

    def __init__(
        self,
        transactions: TransactionRepository,
        categories: CategoryLookup,
        rules: RecurringRuleLookup,
        clock: Clock,
    ) -> None:
        self._transactions = transactions
        self._categories = categories
        self._rules = rules
        self._clock = clock

    async def execute(self, user_id: uuid.UUID, data: UpsertTransactionInput) -> None:
        existing = await self._transactions.get(data.id)
        # Un movimiento ajeno se trata igual que uno inexistente: no se revela que existe.
        if existing is not None and existing.user_id != user_id:
            raise TransactionNotFoundError

        type_ = validate_type(data.type)
        status = validate_status(data.status)
        amount = validate_amount(data.amount_minor)
        occurred_on = validate_date(data.occurred_on, self._clock.today())
        description = clean_description(data.description)
        note = clean_note(data.note)
        tags = normalize_tags(data.tags)
        if status == PENDING and data.recurring_rule_id is None:
            raise PendingWithoutRuleError

        if existing is not None:
            if existing.type != type_:
                raise TransactionTypeLockedError
            if existing.recurring_rule_id != data.recurring_rule_id:
                raise RecurrenceLinkLockedError
            if existing.deleted_at is not None and existing.recurring_rule_id is not None:
                # Una ocurrencia eliminada u omitida no se vuelve a generar (HU09 regla 5).
                raise OccurrenceDeletedError

        await self._check_category(user_id, data.category_id, type_)
        if data.recurring_rule_id is not None:
            rule_state = await self._rules.state(user_id, data.recurring_rule_id)
            if rule_state is None:
                raise InvalidRecurringRuleError
            # Un dispositivo sin conexión pudo generar un pendiente antes de enterarse de que la
            # regla se eliminó (HU09 regla 8). Los ya confirmados se conservan; los pendientes no.
            if rule_state == "deleted" and status == PENDING:
                raise RuleDeletedError

        if existing is None:
            await self._transactions.add(
                Transaction(
                    id=data.id,
                    user_id=user_id,
                    type=type_,
                    amount_minor=amount,
                    category_id=data.category_id,
                    occurred_on=occurred_on,
                    created_at=data.created_at,
                    description=description,
                    note=note,
                    tags=tags,
                    status=status,
                    recurring_rule_id=data.recurring_rule_id,
                )
            )
            return

        await self._transactions.update(
            replace(
                existing,  # conserva `created_at`, `type` y la regla: no se editan
                amount_minor=amount,
                category_id=data.category_id,
                occurred_on=occurred_on,
                description=description,
                note=note,
                tags=tags,
                status=status,
                deleted_at=None,  # si estaba eliminado, esto es un "Deshacer"
            )
        )

    async def _check_category(self, user_id: uuid.UUID, category_id: uuid.UUID, type_: str) -> None:
        category_type = await self._categories.active_type(user_id, category_id)
        if category_type is None:
            raise InvalidCategoryError
        if category_type != type_:
            raise CategoryTypeMismatchError(type_)
