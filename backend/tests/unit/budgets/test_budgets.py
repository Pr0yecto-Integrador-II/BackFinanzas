import uuid
from datetime import date

import pytest

from app.modules.budgets.domain.errors import (
    BudgetNotFoundError,
    DuplicateBudgetError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidEffectiveFromError,
    NotExpenseCategoryError,
)
from tests.unit.budgets.fakes import World


async def test_definir_presupuesto_de_alimentacion() -> None:
    w = World()
    bid = await w.create()
    b = w.repo.items[bid]
    assert (b.amount_minor, b.effective_from, b.user_id) == (60_000_000, date(2026, 10, 1), w.user)


@pytest.mark.parametrize(
    ("over", "error"),
    [
        ({"amount_minor": 0}, InvalidAmountError),
        ({"amount_minor": 1_000_000_000_000_000}, InvalidAmountError),
        ({"effective_from": date(2026, 10, 15)}, InvalidEffectiveFromError),
        ({"category_id": uuid.uuid4()}, InvalidCategoryError),
    ],
)
async def test_validaciones(over: dict[str, object], error: type[Exception]) -> None:
    with pytest.raises(error):
        await World().create(**over)


async def test_solo_categorias_de_gasto() -> None:
    w = World()
    with pytest.raises(NotExpenseCategoryError):
        await w.create(category_id=w.income_cat)


async def test_cambiar_desde_octubre_conserva_septiembre() -> None:
    w = World()
    sept = await w.create(effective_from=date(2026, 9, 1))
    octo = await w.create(effective_from=date(2026, 10, 1), amount_minor=70_000_000)
    assert w.repo.items[sept].amount_minor == 60_000_000
    assert w.repo.items[octo].amount_minor == 70_000_000


async def test_un_presupuesto_por_categoria_y_mes() -> None:
    w = World()
    await w.create()
    with pytest.raises(DuplicateBudgetError):
        await w.create()


async def test_editar_el_monto_conserva_created_at_y_no_choca_consigo_mismo() -> None:
    w = World()
    bid = await w.create()
    before = w.repo.items[bid]
    await w.upsert.execute(w.user, w.input(id=bid, amount_minor=1, created_at=w.clock.now()))
    after = w.repo.items[bid]
    assert after.amount_minor == 1 and after.created_at == before.created_at


async def test_eliminado_libera_el_mes_y_no_se_edita() -> None:
    w = World()
    bid = await w.create()
    await w.delete.execute(w.user, bid)
    assert w.repo.items[bid].deleted_at == w.clock.now()
    await w.create()  # el mes quedó libre
    with pytest.raises(BudgetNotFoundError):
        await w.upsert.execute(w.user, w.input(id=bid))


async def test_presupuesto_ajeno_se_trata_como_inexistente() -> None:
    w = World()
    bid = await w.create()
    with pytest.raises(BudgetNotFoundError):
        await w.upsert.execute(uuid.uuid4(), w.input(id=bid))
    await w.delete.execute(uuid.uuid4(), bid)
    assert w.repo.items[bid].deleted_at is None


async def test_eliminar_es_idempotente() -> None:
    w = World()
    await w.delete.execute(w.user, uuid.uuid4())
    bid = await w.create()
    await w.delete.execute(w.user, bid)
    first = w.repo.items[bid].deleted_at
    w.clock.advance(minutes=1)
    await w.delete.execute(w.user, bid)
    assert w.repo.items[bid].deleted_at == first
