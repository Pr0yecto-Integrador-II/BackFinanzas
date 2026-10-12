import uuid
from datetime import UTC, date, datetime

import pytest

from app.modules.recurring.domain.errors import (
    CategoryTypeMismatchError,
    DescriptionTooLongError,
    EndBeforeStartError,
    EndConflictError,
    GenerateFromBeforeStartError,
    GenerateFromMovedBackError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidFrequencyError,
    InvalidMaxOccurrencesError,
    InvalidModeError,
    InvalidTypeError,
    RuleNotFoundError,
)
from tests.unit.recurring.fakes import World


async def test_crear_la_regla_del_arriendo_mensual_automatica() -> None:
    w = World()
    rid = await w.create(description="Arriendo")
    rule = w.repo.items[rid]
    assert (rule.type, rule.amount_minor, rule.frequency, rule.mode) == (
        "expense", 120_000_000, "monthly", "auto"
    )  # fmt: skip
    assert rule.user_id == w.user and rule.paused_at is None and rule.description == "Arriendo"


@pytest.mark.parametrize("frequency", ["daily", "weekly", "biweekly", "monthly", "yearly"])
async def test_las_cinco_frecuencias(frequency: str) -> None:
    await World().create(frequency=frequency)


@pytest.mark.parametrize("mode", ["auto", "confirm"])
async def test_los_dos_modos(mode: str) -> None:
    await World().create(mode=mode)


async def test_regla_de_ingreso_quincenal_con_fuente_de_ingreso() -> None:
    w = World()
    await w.create(type="income", category_id=w.income_cat, frequency="biweekly")


@pytest.mark.parametrize(
    ("over", "error"),
    [
        ({"type": "transfer"}, InvalidTypeError),
        ({"amount_minor": 0}, InvalidAmountError),
        ({"amount_minor": 1_000_000_000_000_000}, InvalidAmountError),
        ({"frequency": "every-3-months"}, InvalidFrequencyError),  # fuera de alcance
        ({"mode": "manual"}, InvalidModeError),
        ({"description": "x" * 101}, DescriptionTooLongError),
    ],
)
async def test_validaciones_de_campos(over: dict[str, object], error: type[Exception]) -> None:
    w = World()
    with pytest.raises(error):
        await w.create(**over)
    assert not w.repo.items


async def test_la_categoria_debe_ser_del_usuario_activa_y_del_mismo_tipo() -> None:
    w = World()
    ajena = w.categories.add(uuid.uuid4(), "expense")
    with pytest.raises(InvalidCategoryError):
        await w.create(category_id=ajena)
    with pytest.raises(InvalidCategoryError):
        await w.create(category_id=uuid.uuid4())
    with pytest.raises(CategoryTypeMismatchError) as e:
        await w.create(type="expense", category_id=w.income_cat)
    assert e.value.message == "La categoría debe ser de tipo gasto."


async def test_el_inicio_puede_ser_pasado_o_futuro() -> None:
    w = World()
    await w.create(start_on=date(2020, 1, 31), generate_from=date(2020, 1, 31))
    await w.create(start_on=date(2030, 1, 1), generate_from=date(2030, 1, 1))


# ---------- fin: por fecha o por repeticiones ----------


async def test_sin_fin_fin_por_fecha_o_fin_por_repeticiones() -> None:
    w = World()
    await w.create()
    await w.create(end_on=date(2027, 10, 5))
    await w.create(max_occurrences=12)
    await w.create(end_on=date(2026, 10, 5))  # mismo día que el inicio: una sola ocurrencia


async def test_no_se_admiten_ambos_tipos_de_fin() -> None:
    with pytest.raises(EndConflictError):
        await World().create(end_on=date(2027, 1, 1), max_occurrences=3)


@pytest.mark.parametrize("n", [0, -1, 100_001])
async def test_repeticiones_fuera_de_rango(n: int) -> None:
    with pytest.raises(InvalidMaxOccurrencesError):
        await World().create(max_occurrences=n)


async def test_el_fin_no_puede_ser_anterior_al_inicio() -> None:
    with pytest.raises(EndBeforeStartError):
        await World().create(end_on=date(2026, 10, 4))


# ---------- pausar y reanudar: generate_from ----------


async def test_generate_from_no_puede_ser_anterior_al_inicio() -> None:
    with pytest.raises(GenerateFromBeforeStartError):
        await World().create(generate_from=date(2026, 10, 4))


async def test_pausar_guarda_paused_at() -> None:
    w = World()
    rid = await w.create()
    paused = datetime(2026, 11, 1, tzinfo=UTC)
    await w.upsert.execute(w.user, w.input(id=rid, paused_at=paused))
    assert w.repo.items[rid].paused_at == paused


async def test_reanudar_avanza_generate_from_para_saltar_el_periodo_pausado() -> None:
    w = World()
    rid = await w.create()
    await w.upsert.execute(w.user, w.input(id=rid, paused_at=datetime(2026, 11, 1, tzinfo=UTC)))
    await w.upsert.execute(
        w.user, w.input(id=rid, paused_at=None, generate_from=date(2026, 12, 20))
    )
    rule = w.repo.items[rid]
    assert rule.paused_at is None and rule.generate_from == date(2026, 12, 20)


async def test_generate_from_nunca_retrocede() -> None:
    w = World()
    rid = await w.create(generate_from=date(2026, 12, 20))
    with pytest.raises(GenerateFromMovedBackError):
        await w.upsert.execute(w.user, w.input(id=rid, generate_from=date(2026, 10, 5)))
    assert w.repo.items[rid].generate_from == date(2026, 12, 20)
    await w.upsert.execute(w.user, w.input(id=rid, generate_from=date(2026, 12, 20)))  # igual: ok


async def test_regla_creada_y_pausada_sin_conexion_llega_con_generate_from_futuro() -> None:
    """El cliente envía solo el estado final: generate_from puede superar a start_on."""
    await World().create(generate_from=date(2026, 12, 20))


# ---------- editar ----------


async def test_editar_cambia_la_plantilla_y_conserva_created_at() -> None:
    w = World()
    rid = await w.create()
    original = w.repo.items[rid]
    await w.upsert.execute(
        w.user,
        w.input(
            id=rid,
            amount_minor=130_000_000,
            created_at=datetime(2030, 1, 1, tzinfo=UTC),
            mode="confirm",
        ),
    )
    edited = w.repo.items[rid]
    assert (edited.amount_minor, edited.mode) == (130_000_000, "confirm")
    assert edited.created_at == original.created_at and edited.user_id == w.user


async def test_editar_puede_cambiar_el_tipo_si_la_categoria_coincide() -> None:
    w = World()
    rid = await w.create()
    await w.upsert.execute(w.user, w.input(id=rid, type="income", category_id=w.income_cat))
    assert w.repo.items[rid].type == "income"


async def test_reenviar_el_mismo_cambio_no_duplica() -> None:
    w = World()
    data = w.input()
    await w.upsert.execute(w.user, data)
    await w.upsert.execute(w.user, data)
    assert len(w.repo.items) == 1


async def test_regla_ajena_o_eliminada_se_trata_como_inexistente() -> None:
    w = World()
    otro = uuid.uuid4()
    cat = w.categories.add(otro, "expense")
    ajena = w.input(category_id=cat)
    await w.upsert.execute(otro, ajena)
    with pytest.raises(RuleNotFoundError):
        await w.upsert.execute(w.user, w.input(id=ajena.id))
    assert w.repo.items[ajena.id].user_id == otro

    mia = await w.create()
    await w.delete.execute(w.user, mia)
    with pytest.raises(RuleNotFoundError):
        await w.upsert.execute(w.user, w.input(id=mia))
