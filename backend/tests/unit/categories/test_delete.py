import uuid

import pytest

from app.modules.categories.domain.errors import (
    InvalidReassignmentError,
    LastCategoryOfTypeError,
    ReassignmentRequiredError,
)
from tests.unit.categories.fakes import World


async def two_expense() -> tuple[World, uuid.UUID, uuid.UUID]:
    w = World()
    return w, await w.create("Ocio"), await w.create("Transporte")


async def test_eliminar_una_categoria_sin_uso() -> None:
    w, ocio, _ = await two_expense()
    await w.delete.execute(w.user, ocio)
    assert w.repo.items[ocio].deleted_at == w.clock.now()
    assert w.tx.moves == w.rules.moves == w.budgets.moves == []


async def test_eliminar_con_movimientos_exige_destino() -> None:
    w, ocio, _ = await two_expense()
    w.tx.used.add(ocio)
    with pytest.raises(ReassignmentRequiredError):
        await w.delete.execute(w.user, ocio)
    assert w.repo.items[ocio].deleted_at is None


@pytest.mark.parametrize("module", ["tx", "rules", "budgets"])
async def test_cualquier_modulo_que_la_use_exige_destino(module: str) -> None:
    w, ocio, _ = await two_expense()
    getattr(w, module).used.add(ocio)
    with pytest.raises(ReassignmentRequiredError):
        await w.delete.execute(w.user, ocio)


async def test_reasigna_en_todos_los_modulos_y_elimina() -> None:
    w, ocio, transporte = await two_expense()
    w.tx.used.add(ocio)
    w.rules.used.add(ocio)
    w.budgets.used.add(ocio)
    await w.delete.execute(w.user, ocio, reassign_to=transporte)
    for module in (w.tx, w.rules, w.budgets):
        assert module.moves == [(ocio, transporte)]
    assert w.repo.items[ocio].deleted_at is not None
    assert w.repo.items[transporte].deleted_at is None


async def test_destino_invalido() -> None:
    w, ocio, transporte = await two_expense()
    ingreso = await w.create("Salario", "income")
    otro_usuario = await w.create("Ajena", user=uuid.uuid4())
    w.tx.used.add(ocio)
    for bad in (ocio, ingreso, otro_usuario, uuid.uuid4()):
        with pytest.raises(InvalidReassignmentError):
            await w.delete.execute(w.user, ocio, reassign_to=bad)
    await w.delete.execute(w.user, transporte)  # sin uso, otra categoría
    with pytest.raises(LastCategoryOfTypeError):
        await w.delete.execute(w.user, ocio, reassign_to=transporte)


async def test_destino_eliminado_es_invalido() -> None:
    w, ocio, transporte = await two_expense()
    tercera = await w.create("Tercera")
    await w.delete.execute(w.user, transporte)
    w.tx.used.add(ocio)
    with pytest.raises(InvalidReassignmentError):
        await w.delete.execute(w.user, ocio, reassign_to=transporte)
    await w.delete.execute(w.user, ocio, reassign_to=tercera)


async def test_siempre_queda_una_categoria_de_cada_tipo() -> None:
    w = World()
    solo = await w.create("Salario", "income")
    with pytest.raises(LastCategoryOfTypeError) as e:
        await w.delete.execute(w.user, solo)
    assert e.value.message == "Debes tener al menos una categoría de ingreso."
    assert w.repo.items[solo].deleted_at is None


async def test_el_minimo_se_cuenta_por_tipo() -> None:
    w = World()
    await w.create("Gasto", "expense")
    ingreso = await w.create("Ingreso", "income")
    with pytest.raises(LastCategoryOfTypeError):
        await w.delete.execute(w.user, ingreso)  # hay un gasto, pero no otro ingreso


async def test_las_predeterminadas_se_pueden_eliminar() -> None:
    w = World()
    await w.defaults.execute(w.user)
    await w.delete.execute(w.user, w.by_name("Ocio").id)


async def test_borrar_es_idempotente_inexistente_ajena_o_ya_eliminada() -> None:
    w, ocio, _ = await two_expense()
    ajena = await w.create("Ajena", user=uuid.uuid4())
    await w.delete.execute(w.user, uuid.uuid4())
    await w.delete.execute(w.user, ajena)
    assert w.repo.items[ajena].deleted_at is None  # no se toca lo ajeno
    await w.delete.execute(w.user, ocio)
    first = w.repo.items[ocio].deleted_at
    w.clock.advance(minutes=5)
    await w.delete.execute(w.user, ocio)  # reenviar el mismo cambio no falla ni lo modifica
    assert w.repo.items[ocio].deleted_at == first


async def test_bloquea_las_categorias_del_usuario_antes_de_decidir() -> None:
    w, ocio, _ = await two_expense()
    await w.delete.execute(w.user, ocio)
    assert w.repo.locked == [w.user]
