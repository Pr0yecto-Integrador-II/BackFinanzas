from datetime import date

from app.modules.recurring.domain.errors import (
    DescriptionTooLongError,
    EndBeforeStartError,
    EndConflictError,
    GenerateFromBeforeStartError,
    GenerateFromMovedBackError,
    InvalidAmountError,
    InvalidFrequencyError,
    InvalidMaxOccurrencesError,
    InvalidModeError,
    InvalidTypeError,
)

EXPENSE = "expense"
INCOME = "income"
FREQUENCIES = frozenset({"daily", "weekly", "biweekly", "monthly", "yearly"})
MODES = frozenset({"auto", "confirm"})

MAX_AMOUNT_MINOR = 999_999_999_999_999
MAX_DESCRIPTION = 100
MAX_OCCURRENCES = 100_000  # tope contra abusos; no lo fija el Blueprint (D-44)


def validate_type(type_: str) -> str:
    if type_ not in (EXPENSE, INCOME):
        raise InvalidTypeError
    return type_


def validate_amount(amount_minor: int) -> int:
    if isinstance(amount_minor, bool) or not 1 <= amount_minor <= MAX_AMOUNT_MINOR:
        raise InvalidAmountError
    return amount_minor


def clean_description(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if len(text) > MAX_DESCRIPTION:
        raise DescriptionTooLongError
    return text or None


def validate_frequency(frequency: str) -> str:
    if frequency not in FREQUENCIES:
        raise InvalidFrequencyError
    return frequency


def validate_mode(mode: str) -> str:
    if mode not in MODES:
        raise InvalidModeError
    return mode


def validate_end(start_on: date, end_on: date | None, max_occurrences: int | None) -> None:
    """El fin es opcional: por fecha **o** por repeticiones, nunca ambos (HU09 regla 1)."""
    if end_on is not None and max_occurrences is not None:
        raise EndConflictError
    if max_occurrences is not None and not 1 <= max_occurrences <= MAX_OCCURRENCES:
        raise InvalidMaxOccurrencesError
    if end_on is not None and end_on < start_on:
        raise EndBeforeStartError


def validate_generate_from(
    start_on: date, generate_from: date, previous_generate_from: date | None
) -> None:
    if generate_from < start_on:
        raise GenerateFromBeforeStartError
    # Al reanudar una regla pausada `generate_from` salta hacia adelante; nunca hacia atrás,
    # o se regenerarían las fechas del periodo pausado (HU09 regla 7).
    if previous_generate_from is not None and generate_from < previous_generate_from:
        raise GenerateFromMovedBackError
