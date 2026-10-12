import unicodedata

from app.modules.categories.domain.catalog import COLORS, ICONS, TYPES
from app.modules.categories.domain.errors import (
    InvalidCategoryNameError,
    InvalidCategoryTypeError,
    InvalidColorError,
    InvalidIconError,
)

MAX_NAME = 30


def clean_name(raw: str) -> str:
    name = raw.strip()
    if not 1 <= len(name) <= MAX_NAME:
        raise InvalidCategoryNameError
    return name


def name_key(name: str) -> str:
    """Minúsculas y sin tildes: "Café" y "cafe" son el mismo nombre (HU08 regla 2)."""
    decomposed = unicodedata.normalize("NFKD", name.strip())
    key = "".join(c for c in decomposed if not unicodedata.combining(c)).lower()
    if len(key) > MAX_NAME:  # algunos caracteres (ligaduras) se expanden al normalizar
        raise InvalidCategoryNameError
    return key


def validate_type(type_: str) -> str:
    if type_ not in TYPES:
        raise InvalidCategoryTypeError
    return type_


def validate_icon(icon: str) -> str:
    if icon not in ICONS:
        raise InvalidIconError
    return icon


def validate_color(color: str) -> str:
    color = color.upper()
    if color not in COLORS:
        raise InvalidColorError
    return color
