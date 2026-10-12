import uuid

from tests.unit.recurring.fakes import World


async def test_eliminar_descarta_los_pendientes_y_marca_la_baja_logica() -> None:
    w = World()
    rid = await w.create()
    await w.delete.execute(w.user, rid)
    assert w.repo.items[rid].deleted_at == w.clock.now()
    assert w.pending.discarded == [(w.user, rid, w.clock.now())]


async def test_eliminar_es_idempotente() -> None:
    w = World()
    rid = await w.create()
    await w.delete.execute(w.user, rid)
    first = w.repo.items[rid].deleted_at
    w.clock.advance(minutes=1)
    await w.delete.execute(w.user, rid)
    assert w.repo.items[rid].deleted_at == first
    assert len(w.pending.discarded) == 1  # no se vuelve a barrer
    await w.delete.execute(w.user, uuid.uuid4())


async def test_no_se_elimina_la_regla_de_otro_usuario() -> None:
    w = World()
    otro = uuid.uuid4()
    cat = w.categories.add(otro, "expense")
    data = w.input(category_id=cat)
    await w.upsert.execute(otro, data)
    await w.delete.execute(w.user, data.id)
    assert w.repo.items[data.id].deleted_at is None and w.pending.discarded == []
