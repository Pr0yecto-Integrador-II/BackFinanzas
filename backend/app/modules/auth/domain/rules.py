import re

from app.modules.auth.domain.errors import (
    InvalidCurrencyError,
    InvalidEmailError,
    PasswordLengthError,
    PasswordMismatchError,
    WeakPasswordError,
)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Monedas ISO 4217 activas más usadas. Para agregar una, basta con sumarla aquí.
CURRENCIES = frozenset(
    "COP USD EUR MXN ARS BRL CLP PEN UYU BOB PYG VES CRC GTQ HNL NIO PAB DOP CUP "  # noqa: SIM905
    "GBP CHF JPY CNY CAD AUD NZD SEK NOK DKK PLN CZK HUF RON UAH TRY RUB INR PKR "
    "BDT IDR PHP THB VND MYR SGD KRW HKD TWD ILS AED SAR QAR KWD EGP MAD ZAR NGN "
    "KES GHS".split()
)


def normalize_email(raw: str) -> str:
    email = raw.strip().lower()
    if len(email) > 254 or not _EMAIL.match(email):
        raise InvalidEmailError
    return email


def validate_password(password: str, confirmation: str) -> None:
    if not 8 <= len(password) <= 128:
        raise PasswordLengthError
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise WeakPasswordError
    if password != confirmation:
        raise PasswordMismatchError


def validate_currency(code: str) -> str:
    code = code.strip().upper()
    if code not in CURRENCIES:
        raise InvalidCurrencyError
    return code
