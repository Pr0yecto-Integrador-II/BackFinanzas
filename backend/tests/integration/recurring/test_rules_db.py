import uuid
from datetime import UTC, date, datetime

import pytest

from app.modules.recurring.domain.errors import InvalidCategoryError, RuleNotFoundError
from app.modules.transactions.domain.errors import OccurrenceDeletedError, RuleDeletedError
from tests.integration.recurring.conftest import RuleApi


async def test_guarda_y_lee_todos_los_campos(rules: RuleApi) -> None:
    user = await rules.db.user()
    cat = await rules.db.category(user, "Vivienda")
    data = rules.input(cat, description="Arriendo", end_on=date(2027, 10, 5))
    await rules.upsert.execute(user, data)
    row = await rules.db.row("recurring_rules", data.id)
    assert (row["frequency"], row["mode"], row["start_on"], row["end_on"]) == (
        "monthly", "confirm", date(2026, 10, 5), date(2027, 10, 5)
    )  # fmt: skip
    assert row["max_occurrences"] is None and row["generate_from"] == date(2026, 10, 5)
    assert row["description"] == "Arriendo" and row["user_id"] == user


async def test_pausar_reanudar_y_editar_suben_la_version(rules: RuleApi) -> None:
    user = await rules.db.user()
    cat = await rules.db.category(user, "Vivienda")
    data = rules.input(cat)
    await rules.upsert.execute(user, data)
    v0 = int(str((await rules.db.row("recurring_rules", data.id))["version"]))

    await rules.upsert.execute(
        user, rules.input(cat, id=data.id, paused_at=datetime(2026, 11, 1, tzinfo=UTC))
    )
    paused = await rules.db.row("recurring_rules", data.id)
    assert paused["paused_at"] is not None and int(str(paused["version"])) > v0

    await rules.upsert.execute(
        user, rules.input(cat, id=data.id, paused_at=None, generate_from=date(2026, 12, 20))
    )
    resumed = await rules.db.row("recurring_rules", data.id)
    assert resumed["paused_at"] is None and resumed["generate_from"] == date(2026, 12, 20)
    assert resumed["created_at"] == paused["created_at"]


async def test_categoria_ajena_o_eliminada_se_rechaza(rules: RuleApi) -> None:
    ana, luis = await rules.db.user("ana@correo.com"), await rules.db.user("luis@correo.com")
    de_luis = await rules.db.category(luis, "Vivienda")
    with pytest.raises(InvalidCategoryError):
        await rules.upsert.execute(ana, rules.input(de_luis))


async def test_no_se_edita_ni_elimina_la_regla_de_otro_usuario(rules: RuleApi) -> None:
    ana, luis = await rules.db.user("ana@correo.com"), await rules.db.user("luis@correo.com")
    cat_ana, cat_luis = await rules.db.category(ana, "V"), await rules.db.category(luis, "V")
    data = rules.input(cat_luis)
    await rules.upsert.execute(luis, data)
    with pytest.raises(RuleNotFoundError):
        await rules.upsert.execute(ana, rules.input(cat_ana, id=data.id, amount_minor=1))
    await rules.delete.execute(ana, data.id)
    row = await rules.db.row("recurring_rules", data.id)
    assert (
        row["user_id"] == luis and row["deleted_at"] is None and row["amount_minor"] == 120_000_000
    )


async def test_eliminar_la_regla_descarta_pendientes_y_conserva_lo_registrado(
    rules: RuleApi,
) -> None:
    user = await rules.db.user()
    cat = await rules.db.category(user, "Servicios")
    rule = rules.input(cat, mode="confirm")
    await rules.upsert.execute(user, rule)

    def tx(**over: object):  # type: ignore[no-untyped-def]
        return rules.tx.input(cat, recurring_rule_id=rule.id, **over)

    pending, confirmed = tx(status="pending"), tx(occurred_on=date(2026, 9, 5))
    other_rule = rules.input(cat)
    await rules.upsert.execute(user, other_rule)
    pending_other = rules.tx.input(cat, recurring_rule_id=other_rule.id, status="pending")
    for t in (pending, confirmed, pending_other):
        await rules.tx.upsert.execute(user, t)
    v_before = int(str((await rules.db.row("transactions", pending.id))["version"]))

    await rules.delete.execute(user, rule.id)

    assert (await rules.db.row("recurring_rules", rule.id))["deleted_at"] is not None
    gone = await rules.db.row("transactions", pending.id)
    assert gone["deleted_at"] is not None and int(str(gone["version"])) > v_before
    kept = await rules.db.row("transactions", confirmed.id)
    assert kept["deleted_at"] is None and kept["recurring_rule_id"] == rule.id  # historial intacto
    other = await rules.db.row("transactions", pending_other.id)
    assert other["deleted_at"] is None  # el pendiente de OTRA regla no se toca


async def test_tras_eliminar_la_regla_no_admite_pendientes_nuevos_pero_si_confirmados(
    rules: RuleApi,
) -> None:
    user = await rules.db.user()
    cat = await rules.db.category(user, "Servicios")
    rule = rules.input(cat)
    await rules.upsert.execute(user, rule)
    await rules.delete.execute(user, rule.id)

    with pytest.raises(RuleDeletedError):
        await rules.tx.upsert.execute(
            user, rules.tx.input(cat, recurring_rule_id=rule.id, status="pending")
        )
    await rules.tx.upsert.execute(user, rules.tx.input(cat, recurring_rule_id=rule.id))


async def test_el_pendiente_descartado_no_resucita_si_otro_dispositivo_lo_reenvia(
    rules: RuleApi,
) -> None:
    user = await rules.db.user()
    cat = await rules.db.category(user, "Servicios")
    rule = rules.input(cat)
    await rules.upsert.execute(user, rule)
    pending = rules.tx.input(cat, recurring_rule_id=rule.id, status="pending")
    await rules.tx.upsert.execute(user, pending)
    await rules.delete.execute(user, rule.id)
    with pytest.raises((OccurrenceDeletedError, RuleDeletedError)):
        await rules.tx.upsert.execute(user, pending)


async def test_borrar_una_categoria_mueve_tambien_las_reglas(rules: RuleApi) -> None:
    """Integra HU08 con HU09."""
    user = await rules.db.user()
    ocio, otra = await rules.db.category(user, "Ocio"), await rules.db.category(user, "Otra")
    data = rules.input(ocio)
    await rules.upsert.execute(user, data)
    await rules.db.delete.execute(user, ocio, reassign_to=otra)
    assert (await rules.db.row("recurring_rules", data.id))["category_id"] == otra


async def test_eliminar_es_idempotente_con_postgres_real(rules: RuleApi) -> None:
    user = await rules.db.user()
    cat = await rules.db.category(user, "Servicios")
    rule = rules.input(cat)
    await rules.upsert.execute(user, rule)
    await rules.delete.execute(user, rule.id)
    first = (await rules.db.row("recurring_rules", rule.id))["deleted_at"]
    await rules.delete.execute(user, rule.id)
    await rules.delete.execute(user, uuid.uuid4())
    assert (await rules.db.row("recurring_rules", rule.id))["deleted_at"] == first
