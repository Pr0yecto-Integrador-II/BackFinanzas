import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.modules.transactions.domain.errors import (
    InvalidCategoryError,
    InvalidRecurringRuleError,
    OccurrenceDeletedError,
    TransactionNotFoundError,
)
from tests.integration.transactions.conftest import TxApi


async def test_guarda_y_lee_todos_los_campos_con_etiquetas_normalizadas(api: TxApi) -> None:
    user = await api.db.user()
    cat = await api.db.category(user, "Comida")
    data = api.input(
        cat, description="Almuerzo", note="con el equipo", tags=["#Trabajo", "Viaje X"]
    )
    await api.upsert.execute(user, data)
    row = await api.db.row("transactions", data.id)
    assert row["tags"] == ["trabajo", "viaje-x"]
    assert (row["amount_minor"], row["description"], row["status"]) == (
        2_500_000, "Almuerzo", "confirmed"
    )  # fmt: skip
    assert row["user_id"] == user and row["deleted_at"] is None


async def test_editar_sube_la_version_y_conserva_created_at_y_tipo(api: TxApi) -> None:
    user = await api.db.user()
    cat = await api.db.category(user, "Comida")
    data = api.input(cat)
    await api.upsert.execute(user, data)
    before = await api.db.row("transactions", data.id)

    await api.upsert.execute(
        user,
        api.input(cat, id=data.id, amount_minor=1, created_at=datetime(2030, 1, 1, tzinfo=UTC)),
    )
    after = await api.db.row("transactions", data.id)
    assert after["amount_minor"] == 1
    assert int(str(after["version"])) > int(str(before["version"]))
    assert after["created_at"] == before["created_at"] and after["type"] == "expense"


async def test_eliminar_y_deshacer_con_postgres_real(api: TxApi) -> None:
    user = await api.db.user()
    cat = await api.db.category(user, "Comida")
    data = api.input(cat, amount_minor=4_000_000, tags=["viaje"])
    await api.upsert.execute(user, data)
    v0 = int(str((await api.db.row("transactions", data.id))["version"]))

    await api.delete.execute(user, data.id)
    deleted = await api.db.row("transactions", data.id)
    assert deleted["deleted_at"] is not None  # baja lógica: la fila sigue ahí
    v1 = int(str(deleted["version"]))
    assert v1 > v0  # así el borrado llega a los demás dispositivos (pull)

    await api.upsert.execute(user, data)  # Deshacer
    restored = await api.db.row("transactions", data.id)
    assert restored["deleted_at"] is None and restored["amount_minor"] == 4_000_000
    assert restored["tags"] == ["viaje"] and int(str(restored["version"])) > v1


async def test_categoria_de_otro_usuario_o_eliminada_se_rechaza(api: TxApi) -> None:
    ana, luis = await api.db.user("ana@correo.com"), await api.db.user("luis@correo.com")
    de_luis = await api.db.category(luis, "Comida")
    mia = await api.db.category(ana, "Ocio")
    otra = await api.db.category(ana, "Otra")
    with pytest.raises(InvalidCategoryError):
        await api.upsert.execute(ana, api.input(de_luis))
    await api.db.delete.execute(ana, mia)
    with pytest.raises(InvalidCategoryError):
        await api.upsert.execute(ana, api.input(mia))
    await api.upsert.execute(ana, api.input(otra))


async def test_no_se_edita_ni_elimina_el_movimiento_de_otro_usuario(api: TxApi) -> None:
    ana, luis = await api.db.user("ana@correo.com"), await api.db.user("luis@correo.com")
    cat_luis, cat_ana = await api.db.category(luis, "Comida"), await api.db.category(ana, "Comida")
    data = api.input(cat_luis)
    await api.upsert.execute(luis, data)

    with pytest.raises(TransactionNotFoundError):
        await api.upsert.execute(ana, api.input(cat_ana, id=data.id, amount_minor=1))
    await api.delete.execute(ana, data.id)
    row = await api.db.row("transactions", data.id)
    assert row["user_id"] == luis and row["amount_minor"] == 2_500_000 and row["deleted_at"] is None


async def test_regla_recurrente_real_ajena_o_inexistente(api: TxApi) -> None:
    ana, luis = await api.db.user("ana@correo.com"), await api.db.user("luis@correo.com")
    cat = await api.db.category(ana, "Vivienda")
    cat_luis = await api.db.category(luis, "Vivienda")
    mia, de_luis = await api.db.rule(ana, cat), await api.db.rule(luis, cat_luis)

    await api.upsert.execute(ana, api.input(cat, recurring_rule_id=mia))
    for bad in (de_luis, uuid.uuid4()):
        with pytest.raises(InvalidRecurringRuleError):
            await api.upsert.execute(ana, api.input(cat, recurring_rule_id=bad))


async def test_una_regla_eliminada_sigue_valiendo_para_sus_ocurrencias(api: TxApi) -> None:
    user = await api.db.user()
    cat = await api.db.category(user, "Vivienda")
    rule = await api.db.rule(user, cat)
    await api.db.s.execute(text("UPDATE recurring_rules SET deleted_at = now()"))
    await api.upsert.execute(user, api.input(cat, recurring_rule_id=rule))


async def test_ocurrencia_recurrente_eliminada_no_resucita(api: TxApi) -> None:
    user = await api.db.user()
    cat = await api.db.category(user, "Vivienda")
    rule = await api.db.rule(user, cat)
    data = api.input(cat, recurring_rule_id=rule)
    await api.upsert.execute(user, data)
    await api.delete.execute(user, data.id)
    with pytest.raises(OccurrenceDeletedError):
        await api.upsert.execute(user, data)
    assert (await api.db.row("transactions", data.id))["deleted_at"] is not None


async def test_eliminar_la_categoria_la_reasigna_a_los_movimientos_creados_por_este_caso_de_uso(
    api: TxApi,
) -> None:
    """Integra HU08 con HU04: los movimientos reales siguen a su categoría reasignada."""
    user = await api.db.user()
    ocio, transporte = await api.db.category(user, "Ocio"), await api.db.category(user, "Transp")
    data = api.input(ocio)
    await api.upsert.execute(user, data)
    await api.db.delete.execute(user, ocio, reassign_to=transporte)
    assert (await api.db.row("transactions", data.id))["category_id"] == transporte
