import uuid
from datetime import UTC, date, datetime

import pytest

from app.modules.transactions.domain.errors import (
    CategoryTypeMismatchError,
    DescriptionTooLongError,
    FutureDateError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidRecurringRuleError,
    InvalidStatusError,
    InvalidTagError,
    InvalidTypeError,
    NoteTooLongError,
    PendingWithoutRuleError,
    RecurrenceLinkLockedError,
    RuleDeletedError,
    TooManyTagsError,
    TransactionNotFoundError,
    TransactionTypeLockedError,
)
from app.modules.transactions.domain.rules import normalize_tag, normalize_tags
from tests.unit.transactions.fakes import World

# ---------- HU04 / HU05: registrar ----------


async def test_registrar_gasto_con_valores_minimos() -> None:
    w = World()
    tid = await w.create()
    tx = w.repo.items[tid]
    assert (tx.type, tx.amount_minor, tx.status) == ("expense", 2_500_000, "confirmed")
    assert tx.description is None and tx.note is None and tx.tags == []
    assert tx.user_id == w.user and tx.recurring_rule_id is None


async def test_registrar_ingreso_con_una_fuente_de_ingreso() -> None:
    w = World()
    tid = await w.create(type="income", category_id=w.income_cat, amount_minor=350_000_000)
    assert w.repo.items[tid].type == "income"


async def test_un_gasto_no_acepta_una_fuente_de_ingreso_y_al_reves() -> None:
    w = World()
    with pytest.raises(CategoryTypeMismatchError) as e:
        await w.create(type="expense", category_id=w.income_cat)
    assert e.value.message == "La categoría debe ser de tipo gasto."
    with pytest.raises(CategoryTypeMismatchError) as e2:
        await w.create(type="income", category_id=w.expense_cat)
    assert e2.value.message == "La categoría debe ser de tipo ingreso."
    assert not w.repo.items


async def test_categoria_inexistente_ajena_o_eliminada_se_rechaza() -> None:
    w = World()
    ajena = w.categories.add(uuid.uuid4(), "expense")
    for bad in (uuid.uuid4(), ajena):
        with pytest.raises(InvalidCategoryError):
            await w.create(category_id=bad)


@pytest.mark.parametrize("amount", [0, -1, 1_000_000_000_000_000])
async def test_monto_fuera_de_rango(amount: int) -> None:
    with pytest.raises(InvalidAmountError):
        await World().create(amount_minor=amount)


@pytest.mark.parametrize("amount", [1, 999_999_999_999_999])
async def test_monto_en_los_extremos_validos(amount: int) -> None:
    await World().create(amount_minor=amount)


async def test_el_monto_no_acepta_booleanos() -> None:
    with pytest.raises(InvalidAmountError):
        await World().create(amount_minor=True)


async def test_fecha_de_hoy_valida_y_futura_rechazada() -> None:
    w = World()
    await w.create(occurred_on=date(2026, 10, 12))
    await w.create(occurred_on=date(2020, 1, 1))
    with pytest.raises(FutureDateError) as e:
        await w.create(occurred_on=date(2026, 10, 14))
    assert e.value.message == "La fecha no puede ser futura."


async def test_se_tolera_un_dia_de_diferencia_por_zona_horaria() -> None:
    """D-14: el servidor no conoce la zona del usuario, así que admite hoy UTC + 1 día."""
    w = World()
    await w.create(occurred_on=date(2026, 10, 13))


@pytest.mark.parametrize(
    ("over", "error"),
    [
        ({"type": "transfer"}, InvalidTypeError),
        ({"status": "draft"}, InvalidStatusError),
        ({"description": "x" * 101}, DescriptionTooLongError),
        ({"note": "x" * 501}, NoteTooLongError),
        ({"status": "pending"}, PendingWithoutRuleError),
    ],
)
async def test_validaciones_de_campos(over: dict[str, object], error: type[Exception]) -> None:
    w = World()
    with pytest.raises(error):
        await w.create(**over)
    assert not w.repo.items


async def test_limites_validos_de_descripcion_y_nota() -> None:
    w = World()
    tid = await w.create(description="d" * 100, note="n" * 500)
    assert len(w.repo.items[tid].description or "") == 100


async def test_descripcion_y_nota_vacias_se_guardan_como_nulas() -> None:
    w = World()
    tid = await w.create(description="   ", note="")
    assert w.repo.items[tid].description is None and w.repo.items[tid].note is None


async def test_descripcion_se_recorta() -> None:
    w = World()
    assert w.repo.items[await w.create(description="  Almuerzo  ")].description == "Almuerzo"


async def test_regla_recurrente_debe_existir_y_ser_del_usuario() -> None:
    w = World()
    with pytest.raises(InvalidRecurringRuleError):
        await w.create(recurring_rule_id=uuid.uuid4())
    ajena = uuid.uuid4()
    w.rules.rules[(uuid.uuid4(), ajena)] = "active"
    with pytest.raises(InvalidRecurringRuleError):
        await w.create(recurring_rule_id=ajena)


async def test_pendiente_solo_si_viene_de_una_regla() -> None:
    w = World()
    rule = w.rule()
    tid = await w.create(status="pending", recurring_rule_id=rule)
    assert w.repo.items[tid].status == "pending"


# ---------- HU10: notas y etiquetas ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("#Viaje Cartagena", "viaje-cartagena"),
        ("#Trabajo", "trabajo"),
        ("reembolsable", "reembolsable"),
        ("  ##Café   con  leche ", "café-con-leche"),
        ("A" * 20, "a" * 20),
    ],
)
def test_normalizacion_de_etiquetas(raw: str, expected: str) -> None:
    assert normalize_tag(raw) == expected


@pytest.mark.parametrize("raw", ["", "#", "   ", "a" * 21, "# - "])
def test_etiqueta_invalida(raw: str) -> None:
    with pytest.raises(InvalidTagError):
        normalize_tag(raw)


def test_etiquetas_repetidas_tras_normalizar_se_unifican_conservando_orden() -> None:
    assert normalize_tags(["#Trabajo", "viaje", "trabajo", "TRABAJO"]) == ["trabajo", "viaje"]


async def test_agregar_nota_y_etiquetas() -> None:
    w = World()
    tid = await w.create(note="Almuerzo con el equipo", tags=["#Trabajo", "reembolsable"])
    tx = w.repo.items[tid]
    assert tx.tags == ["trabajo", "reembolsable"] and tx.note == "Almuerzo con el equipo"


async def test_maximo_5_etiquetas() -> None:
    w = World()
    await w.create(tags=["a", "b", "c", "d", "e"])
    with pytest.raises(TooManyTagsError) as e:
        await w.create(tags=["a", "b", "c", "d", "e", "f"])
    assert e.value.message == "Máximo 5 etiquetas por movimiento."


async def test_seis_etiquetas_donde_una_se_repite_son_cinco_validas() -> None:
    await World().create(tags=["a", "b", "c", "d", "e", "#A"])


# ---------- HU06: editar ----------


async def test_corregir_monto_y_categoria() -> None:
    w = World()
    otra = w.categories.add(w.user, "expense")
    tid = await w.create(amount_minor=5_200_000)
    original = w.repo.items[tid]
    await w.upsert.execute(
        w.user, w.input(id=tid, amount_minor=2_500_000, category_id=otra, note="corregido")
    )
    edited = w.repo.items[tid]
    assert (edited.amount_minor, edited.category_id, edited.note) == (2_500_000, otra, "corregido")
    assert edited.created_at == original.created_at  # el orden del día no cambia (HU11)


async def test_editar_no_permite_cambiar_el_tipo() -> None:
    w = World()
    tid = await w.create()
    with pytest.raises(TransactionTypeLockedError) as e:
        await w.upsert.execute(w.user, w.input(id=tid, type="income", category_id=w.income_cat))
    assert "Elimina el movimiento y crea otro" in e.value.message
    assert w.repo.items[tid].type == "expense"


async def test_editar_ignora_el_created_at_enviado() -> None:
    w = World()
    tid = await w.create()
    await w.upsert.execute(
        w.user, w.input(id=tid, created_at=datetime(2030, 1, 1, tzinfo=UTC), amount_minor=1)
    )
    assert w.repo.items[tid].created_at == datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


async def test_editar_un_movimiento_recurrente_no_cambia_su_regla() -> None:
    w = World()
    rule, other = w.rule(), w.rule()
    tid = await w.create(recurring_rule_id=rule)
    await w.upsert.execute(w.user, w.input(id=tid, recurring_rule_id=rule, amount_minor=104_300))
    assert w.repo.items[tid].amount_minor == 104_300
    with pytest.raises(RecurrenceLinkLockedError):
        await w.upsert.execute(w.user, w.input(id=tid, recurring_rule_id=other))
    with pytest.raises(RecurrenceLinkLockedError):
        await w.upsert.execute(w.user, w.input(id=tid, recurring_rule_id=None))


async def test_confirmar_un_pendiente_cambia_su_estado_y_permite_ajustar_el_monto() -> None:
    w = World()
    rule = w.rule()
    tid = await w.create(status="pending", recurring_rule_id=rule, amount_minor=9_000_000)
    await w.upsert.execute(
        w.user,
        w.input(id=tid, status="confirmed", recurring_rule_id=rule, amount_minor=10_430_000),
    )
    tx = w.repo.items[tid]
    assert (tx.status, tx.amount_minor) == ("confirmed", 10_430_000)


async def test_gana_la_ultima_version_que_llega() -> None:
    w = World()
    tid = await w.create(amount_minor=100)
    await w.upsert.execute(w.user, w.input(id=tid, amount_minor=200))  # dispositivo A
    await w.upsert.execute(w.user, w.input(id=tid, amount_minor=300))  # dispositivo B, después
    assert w.repo.items[tid].amount_minor == 300


async def test_reenviar_el_mismo_cambio_no_duplica() -> None:
    w = World()
    data = w.input()
    await w.upsert.execute(w.user, data)
    await w.upsert.execute(w.user, data)
    assert len(w.repo.items) == 1


async def test_no_se_puede_editar_ni_tomar_un_movimiento_ajeno() -> None:
    w = World()
    otro = uuid.uuid4()
    cat = w.categories.add(otro, "expense")
    ajeno = w.input(category_id=cat)
    await w.upsert.execute(otro, ajeno)
    with pytest.raises(TransactionNotFoundError):
        await w.upsert.execute(w.user, w.input(id=ajeno.id, amount_minor=1))
    assert w.repo.items[ajeno.id].amount_minor == 2_500_000
    assert w.repo.items[ajeno.id].user_id == otro


async def test_el_user_id_nunca_viene_del_cliente() -> None:
    w = World()
    assert not hasattr(w.input(), "user_id")


async def test_una_regla_eliminada_no_admite_nuevos_pendientes_pero_si_confirmados() -> None:
    """HU09 regla 8: un dispositivo sin conexión pudo generar el pendiente antes de enterarse."""
    w = World()
    rule = w.rule()
    w.rules.rules[(w.user, rule)] = "deleted"
    with pytest.raises(RuleDeletedError):
        await w.create(status="pending", recurring_rule_id=rule)
    tid = await w.create(recurring_rule_id=rule)  # ya registrado en automático: se conserva
    assert w.repo.items[tid].recurring_rule_id == rule
