from datetime import date

from app.modules.budgets.domain.errors import InvalidAmountError, InvalidEffectiveFromError

EXPENSE = "expense"
MAX_AMOUNT_MINOR = 999_999_999_999_999


def validate_amount(amount_minor: int) -> int:
    if isinstance(amount_minor, bool) or not 1 <= amount_minor <= MAX_AMOUNT_MINOR:
        raise InvalidAmountError
    return amount_minor


def validate_effective_from(effective_from: date) -> date:
    """Rige desde el primer día del mes elegido (HU14 reglas 1 y 2)."""
    if effective_from.day != 1:
        raise InvalidEffectiveFromError
    return effective_from
