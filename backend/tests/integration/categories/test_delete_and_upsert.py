import dataclasses
import uuid

import pytest
from sqlalchemy import text

from app.modules.categories.application.upsert import UpsertCategoryInput
from app.modules.categories.domain.errors import (
    CategoryNameTakenError,
    CategoryTypeLockedError,
    LastCategoryOfTypeError,
    ReassignmentRequiredError,
)
from app.modules.categories.infrastructure.repository import SqlCategoryRepository
from tests.integration.conftest import Db


async def test_eliminar_con_movimientos_reglas_y_presupuestos_los_pasa_a_la_categoria_elegida(
    db: Db,
) -> None:
    user = await db.user()
    ocio, transporte = await db.category(user, "Ocio"), await db.category(user, "Transporte")
    t_activo, t_borrado = await db.tx(user, ocio), await db.tx(user, ocio, deleted=True)
    rule = await db.rule(user, ocio)
    before = {
        t: int(str((await db.row("transactions", t))["version"])) for t in (t_activo, t_borrado)
    }

    await db.delete.execute(user, ocio, reassign_to=transporte)

    for table, row_id in (("transactions", t_activo), ("transactions", t_borrado),
                          ("recurring_rules", rule)):  # fmt: skip
        assert (await db.row(table, row_id))["category_id"] == transporte
    assert (await db.row("categories", ocio))["deleted_at"] is not None
    assert (await db.row("categories", transporte))["deleted_at"] is None
    # cada fila movida recibe una versión nueva: así llega a los demás dispositivos (D-16)
    for t in (t_activo, t_borrado):
        assert int(str((await db.row("transactions", t))["version"])) > before[t]


async def test_presupuesto_si_el_destino_no_tiene_se_traslada(db: Db) -> None:
    user = await db.user()
    ocio, transporte = await db.category(user, "Ocio"), await db.category(user, "Transporte")
    budget = await db.budget(user, ocio, 600000)
    await db.delete.execute(user, ocio, reassign_to=transporte)
    row = await db.row("budgets", budget)
    assert row["category_id"] == transporte and row["deleted_at"] is None
    assert row["amount_minor"] == 600000


async def test_si_ambas_tenian_presupuesto_se_conserva_el_del_destino(db: Db) -> None:
    user = await db.user()
    ocio, transporte = await db.category(user, "Ocio"), await db.category(user, "Transporte")
    source, target = await db.budget(user, ocio, 100), await db.budget(user, transporte, 900000)
    await db.delete.execute(user, ocio, reassign_to=transporte)
    assert (await db.row("budgets", source))["deleted_at"] is not None
    kept = await db.row("budgets", target)
    assert kept["deleted_at"] is None and kept["amount_minor"] == 900000


async def test_sin_destino_no_se_elimina_una_categoria_en_uso(db: Db) -> None:
    user = await db.user()
    ocio = await db.category(user, "Ocio")
    await db.category(user, "Transporte")
    await db.tx(user, ocio)
    with pytest.raises(ReassignmentRequiredError):
        await db.delete.execute(user, ocio)
    assert (await db.row("categories", ocio))["deleted_at"] is None


async def test_un_movimiento_borrado_no_cuenta_como_uso(db: Db) -> None:
    user = await db.user()
    ocio = await db.category(user, "Ocio")
    await db.category(user, "Transporte")
    await db.tx(user, ocio, deleted=True)
    await db.delete.execute(user, ocio)  # no exige destino


async def test_no_se_tocan_los_datos_de_otro_usuario(db: Db) -> None:
    ana, luis = await db.user("ana@correo.com"), await db.user("luis@correo.com")
    a_ocio, a_trans = await db.category(ana, "Ocio"), await db.category(ana, "Transporte")
    l_ocio = await db.category(luis, "Ocio")
    l_tx = await db.tx(luis, l_ocio)
    await db.tx(ana, a_ocio)

    await db.delete.execute(ana, a_ocio, reassign_to=a_trans)
    assert (await db.row("transactions", l_tx))["category_id"] == l_ocio

    await db.delete.execute(ana, l_ocio)  # intentar borrar la de Luis no hace nada
    assert (await db.row("categories", l_ocio))["deleted_at"] is None


async def test_ultima_categoria_de_un_tipo(db: Db) -> None:
    user = await db.user()
    solo = await db.category(user, "Salario", "income")
    with pytest.raises(LastCategoryOfTypeError):
        await db.delete.execute(user, solo)


async def test_el_nombre_de_una_eliminada_se_puede_reutilizar(db: Db) -> None:
    user = await db.user()
    cafe = await db.category(user, "Café")
    await db.category(user, "Otra")
    await db.delete.execute(user, cafe)
    await db.category(user, "cafe")


async def test_cambiar_el_tipo_bloqueado_por_movimientos_reales(db: Db) -> None:
    user = await db.user()
    cat = await db.category(user, "Ocio")
    await db.tx(user, cat)
    with pytest.raises(CategoryTypeLockedError):
        await db.upsert.execute(
            user,
            UpsertCategoryInput(
                cat,
                "Ocio",
                "income",
                "pets",
                "#F97316",
                (await db.row("categories", cat))["created_at"],  # type: ignore[arg-type]
            ),
        )


async def test_la_base_atrapa_nombres_duplicados_aunque_se_salte_la_revision(db: Db) -> None:
    """Defensa ante dos dispositivos que crean el mismo nombre a la vez."""
    user = await db.user()
    await db.category(user, "Café")
    repo = SqlCategoryRepository(db.s)
    existing = await repo.get((await db.s.execute(text("SELECT id FROM categories"))).scalar_one())
    assert existing is not None
    duplicate = dataclasses.replace(existing, id=uuid.uuid4())
    with pytest.raises(CategoryNameTakenError):
        async with db.s.begin_nested():
            await repo.add(duplicate)
