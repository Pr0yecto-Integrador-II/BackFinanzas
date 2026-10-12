import uuid

import pytest

from app.modules.transactions.domain.errors import OccurrenceDeletedError
from tests.unit.transactions.fakes import World


async def test_eliminar_marca_la_baja_logica_y_no_borra_la_fila() -> None:
    w = World()
    tid = await w.create()
    await w.delete.execute(w.user, tid)
    assert tid in w.repo.items and w.repo.items[tid].deleted_at == w.clock.now()


async def test_eliminar_es_idempotente() -> None:
    w = World()
    tid = await w.create()
    await w.delete.execute(w.user, tid)
    first = w.repo.items[tid].deleted_at
    w.clock.advance(minutes=1)
    await w.delete.execute(w.user, tid)
    assert w.repo.items[tid].deleted_at == first
    await w.delete.execute(w.user, uuid.uuid4())  # inexistente: no falla


async def test_no_se_elimina_lo_ajeno() -> None:
    w = World()
    otro = uuid.uuid4()
    cat = w.categories.add(otro, "expense")
    data = w.input(category_id=cat)
    await w.upsert.execute(otro, data)
    await w.delete.execute(w.user, data.id)
    assert w.repo.items[data.id].deleted_at is None


async def test_deshacer_restablece_el_movimiento_exactamente_como_estaba() -> None:
    w = World()
    tid = await w.create(amount_minor=4_000_000, note="nota", tags=["viaje"])
    before = w.repo.items[tid]
    await w.delete.execute(w.user, tid)
    await w.upsert.execute(
        w.user, w.input(id=tid, amount_minor=4_000_000, note="nota", tags=["viaje"])
    )
    assert w.repo.items[tid] == before


async def test_eliminar_una_ocurrencia_recurrente_no_afecta_a_la_regla() -> None:
    w = World()
    rule = w.rule()
    tid = await w.create(recurring_rule_id=rule)
    await w.delete.execute(w.user, tid)
    assert (w.user, rule) in w.rules.rules


async def test_una_ocurrencia_eliminada_no_se_regenera_aunque_otro_dispositivo_la_envie() -> None:
    """HU09 regla 5: el mismo id determinista no resucita un borrado."""
    w = World()
    rule = w.rule()
    tid = await w.create(recurring_rule_id=rule)
    await w.delete.execute(w.user, tid)
    with pytest.raises(OccurrenceDeletedError):
        await w.upsert.execute(w.user, w.input(id=tid, recurring_rule_id=rule))
    assert w.repo.items[tid].deleted_at is not None
