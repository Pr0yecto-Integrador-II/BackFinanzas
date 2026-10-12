import re
from datetime import date, timedelta

from app.modules.transactions.domain.errors import (
    DescriptionTooLongError,
    FutureDateError,
    InvalidAmountError,
    InvalidStatusError,
    InvalidTagError,
    InvalidTypeError,
    NoteTooLongError,
    TooManyTagsError,
)

EXPENSE = "expense"
INCOME = "income"
CONFIRMED = "confirmed"
PENDING = "pending"

MAX_AMOUNT_MINOR = 999_999_999_999_999  # 13 dígitos enteros + 2 decimales
MAX_DESCRIPTION = 100
MAX_NOTE = 500
MAX_TAGS = 5
MAX_TAG_LENGTH = 20

_WHITESPACE = re.compile(r"\s+")


def validate_type(type_: str) -> str:
    if type_ not in (EXPENSE, INCOME):
        raise InvalidTypeError
    return type_


def validate_status(status: str) -> str:
    if status not in (CONFIRMED, PENDING):
        raise InvalidStatusError
    return status


def validate_amount(amount_minor: int) -> int:
    if isinstance(amount_minor, bool) or not 1 <= amount_minor <= MAX_AMOUNT_MINOR:
        raise InvalidAmountError
    return amount_minor


def validate_date(occurred_on: date, today: date) -> date:
    """El servidor ignora la zona del usuario: se admite hasta hoy UTC + 1 día (D-14)."""
    if occurred_on > today + timedelta(days=1):
        raise FutureDateError
    return occurred_on


def clean_description(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if len(text) > MAX_DESCRIPTION:
        raise DescriptionTooLongError
    return text or None


def clean_note(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if len(text) > MAX_NOTE:
        raise NoteTooLongError
    return text or None


def normalize_tag(raw: str) -> str:
    """ "#Viaje Cartagena" -> "viaje-cartagena" (HU10 regla 2)."""
    text = _WHITESPACE.sub("-", raw.strip().lstrip("#").strip().lower()).strip("-")
    if not 1 <= len(text) <= MAX_TAG_LENGTH:
        raise InvalidTagError
    return text


def normalize_tags(raw_tags: list[str]) -> list[str]:
    """Normaliza, quita repetidas conservando el orden y limita a 5."""
    tags = list(dict.fromkeys(normalize_tag(t) for t in raw_tags))
    if len(tags) > MAX_TAGS:
        raise TooManyTagsError
    return tags
