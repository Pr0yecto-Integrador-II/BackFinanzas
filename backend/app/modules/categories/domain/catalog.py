"""Íconos y colores permitidos, y las categorías predeterminadas (HU01, HU08).

El frontend debe usar exactamente estas claves: el servidor rechaza cualquier otra.
"""

EXPENSE = "expense"
INCOME = "income"
TYPES = frozenset({EXPENSE, INCOME})

ICONS = frozenset(
    {
        "restaurant", "shopping_cart", "directions_bus", "home", "bolt", "water_drop", "wifi",
        "health_and_safety", "school", "sports_esports", "movie", "shopping_bag", "pets",
        "flight", "local_cafe", "fitness_center", "child_care", "card_giftcard", "savings",
        "payments", "work", "laptop", "trending_up", "account_balance", "receipt_long",
        "phone_android", "checkroom", "build", "more_horiz", "paid",
    }
)  # fmt: skip

COLORS = frozenset(
    {
        "#EF4444", "#F97316", "#F59E0B", "#EAB308", "#84CC16", "#22C55E", "#14B8A6", "#06B6D4",
        "#3B82F6", "#6366F1", "#8B5CF6", "#D946EF", "#EC4899", "#78716C", "#64748B",
    }
)  # fmt: skip

# (nombre, tipo, ícono, color)
DEFAULT_CATEGORIES: tuple[tuple[str, str, str, str], ...] = (
    ("Alimentación", EXPENSE, "restaurant", "#F97316"),
    ("Transporte", EXPENSE, "directions_bus", "#3B82F6"),
    ("Vivienda", EXPENSE, "home", "#8B5CF6"),
    ("Servicios", EXPENSE, "bolt", "#EAB308"),
    ("Salud", EXPENSE, "health_and_safety", "#EF4444"),
    ("Educación", EXPENSE, "school", "#6366F1"),
    ("Ocio", EXPENSE, "sports_esports", "#EC4899"),
    ("Compras", EXPENSE, "shopping_bag", "#14B8A6"),
    ("Otros gastos", EXPENSE, "more_horiz", "#64748B"),
    ("Salario", INCOME, "payments", "#22C55E"),
    ("Trabajo independiente", INCOME, "laptop", "#06B6D4"),
    ("Otros ingresos", INCOME, "paid", "#84CC16"),
)
