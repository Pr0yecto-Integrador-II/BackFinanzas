import uuid
from datetime import UTC, date, datetime

import pytest

from app import composition
from app.modules.budgets.application.upsert import UpsertBudgetInput
from app.modules.budgets.domain.errors import DuplicateBudgetError, NotExpenseCategoryError
from tests.integration.conftest import Db


def _input(cat: uuid.UUID, **over: object) -> UpsertBudgetInput:
    base: dict[str, object] = {
        "id": uuid.uuid4(),
        "category_id": cat,
        "amount_minor": 60_000_000,
        "effective_from": date(2026, 10, 1),
        "created_at": datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
    }
    return UpsertBudgetInput(**{**base, **over})  # type: ignore[arg-type]


async def test_guarda_cambia_y_elimina_subiendo_la_version(db: Db) -> None:
    user = await db.user()
    cat = await db.category(user, "Alimentación")
    upsert, delete = composition.upsert_budget(db.s), composition.delete_budget(db.s, db.clock)
    data = _input(cat)
    await upsert.execute(user, data)
    v0 = int(str((await db.row("budgets", data.id))["version"]))
    await upsert.execute(user, _input(cat, id=data.id, amount_minor=70_000_000))
    row = await db.row("budgets", data.id)
    assert row["amount_minor"] == 70_000_000 and int(str(row["version"])) > v0
    await delete.execute(user, data.id)
    assert (await db.row("budgets", data.id))["deleted_at"] is not None


async def test_dos_meses_distintos_conviven_y_el_mismo_mes_se_rechaza(db: Db) -> None:
    user = await db.user()
    cat = await db.category(user, "Alimentación")
    upsert = composition.upsert_budget(db.s)
    await upsert.execute(user, _input(cat, effective_from=date(2026, 9, 1)))
    await upsert.execute(user, _input(cat))
    with pytest.raises(DuplicateBudgetError):
        await upsert.execute(user, _input(cat))


async def test_categoria_de_ingreso_o_ajena_se_rechaza(db: Db) -> None:
    ana, luis = await db.user("ana@correo.com"), await db.user("luis@correo.com")
    ingreso = await db.category(ana, "Sueldo", "income")
    de_luis = await db.category(luis, "Comida")
    upsert = composition.upsert_budget(db.s)
    with pytest.raises(NotExpenseCategoryError):
        await upsert.execute(ana, _input(ingreso))
    with pytest.raises(Exception, match="categoría"):
        await upsert.execute(ana, _input(de_luis))


async def test_eliminar_categoria_reasigna_el_presupuesto(db: Db) -> None:
    user = await db.user()
    origen = await db.category(user, "Comida")
    destino = await db.category(user, "Mercado")
    data = _input(origen)
    await composition.upsert_budget(db.s).execute(user, data)
    from app.modules.budgets.infrastructure.category_referrer import BudgetCategoryReferrer

    await BudgetCategoryReferrer(db.s).move(user, origen, destino, db.clock.now())
    await db.s.flush()
    assert (await db.row("budgets", data.id))["category_id"] == destino
