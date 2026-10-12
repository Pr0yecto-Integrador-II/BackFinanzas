import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from tests.integration.conftest import make_category, make_user


async def _insert_tx(
    conn: AsyncConnection, user: uuid.UUID, cat: uuid.UUID, **over: object
) -> uuid.UUID:
    params: dict[str, object] = {
        "id": uuid.uuid4(),
        "u": user,
        "c": cat,
        "type": "expense",
        "amount": 25000,
        "tags": [],
        "status": "confirmed",
        "now": datetime.now(UTC),
    }
    params.update(over)
    await conn.execute(
        text(
            "INSERT INTO transactions (id, user_id, type, amount_minor, category_id, occurred_on, "
            "tags, status, created_at) VALUES (:id, :u, :type, :amount, :c, '2026-10-01', "
            ":tags, :status, :now)"
        ),
        params,
    )
    return params["id"]  # type: ignore[return-value]


async def test_version_la_asigna_la_base_en_cada_escritura(conn: AsyncConnection) -> None:
    user = await make_user(conn)
    cat = await make_category(conn, user)
    tx = await _insert_tx(conn, user, cat)
    v1 = (
        await conn.execute(text("SELECT version FROM transactions WHERE id=:i"), {"i": tx})
    ).scalar_one()

    await conn.execute(text("UPDATE transactions SET amount_minor = 1 WHERE id=:i"), {"i": tx})
    v2 = (
        await conn.execute(text("SELECT version FROM transactions WHERE id=:i"), {"i": tx})
    ).scalar_one()
    assert v2 > v1

    # un cliente que intente fijar su propia versión es ignorado
    await conn.execute(text("UPDATE transactions SET version = 1 WHERE id=:i"), {"i": tx})
    v3 = (
        await conn.execute(text("SELECT version FROM transactions WHERE id=:i"), {"i": tx})
    ).scalar_one()
    assert v3 > v2


async def test_la_secuencia_de_version_es_global_entre_tablas(conn: AsyncConnection) -> None:
    user = await make_user(conn)
    cat = await make_category(conn, user)
    v_cat = (
        await conn.execute(text("SELECT version FROM categories WHERE id=:i"), {"i": cat})
    ).scalar_one()
    tx = await _insert_tx(conn, user, cat)
    v_tx = (
        await conn.execute(text("SELECT version FROM transactions WHERE id=:i"), {"i": tx})
    ).scalar_one()
    assert v_tx > v_cat


@pytest.mark.parametrize(
    ("over", "motivo"),
    [
        ({"amount": 0}, "monto cero"),
        ({"amount": 1_000_000_000_000_000}, "monto de más de 13 enteros + 2 decimales"),
        ({"tags": ["a", "b", "c", "d", "e", "f"]}, "más de 5 etiquetas"),
        ({"type": "other"}, "tipo inválido"),
        ({"status": "draft"}, "estado inválido"),
    ],
)
async def test_transactions_rechaza_datos_invalidos(
    conn: AsyncConnection, over: dict[str, object], motivo: str
) -> None:
    user = await make_user(conn)
    cat = await make_category(conn, user)
    with pytest.raises(IntegrityError):
        await _insert_tx(conn, user, cat, **over)


async def test_monto_maximo_valido(conn: AsyncConnection) -> None:
    user = await make_user(conn)
    cat = await make_category(conn, user)
    await _insert_tx(conn, user, cat, amount=999_999_999_999_999)


async def test_email_unico(conn: AsyncConnection) -> None:
    await make_user(conn, "ana@correo.com")
    with pytest.raises(IntegrityError):
        await make_user(conn, "ana@correo.com")


async def test_nombre_de_categoria_unico_por_tipo_e_ignora_borradas(conn: AsyncConnection) -> None:
    user = await make_user(conn)
    first = await make_category(conn, user, "cafe", "expense")
    await make_category(conn, user, "cafe", "income")  # otro tipo: permitido
    with pytest.raises(IntegrityError):
        async with conn.begin_nested():
            await make_category(conn, user, "cafe", "expense")
    await conn.execute(text("UPDATE categories SET deleted_at = now() WHERE id=:i"), {"i": first})
    await make_category(conn, user, "cafe", "expense")  # tras borrar, se puede reutilizar


async def test_presupuesto_debe_empezar_el_dia_1_y_ser_unico_si_no_esta_borrado(
    conn: AsyncConnection,
) -> None:
    user = await make_user(conn)
    cat = await make_category(conn, user)

    async def insert(effective: str) -> uuid.UUID:
        bid = uuid.uuid4()
        await conn.execute(
            text(
                "INSERT INTO budgets (id, user_id, category_id, amount_minor, effective_from, "
                "created_at) "
                "VALUES (:id, :u, :c, 600000, :e, now())"
            ),
            {"id": bid, "u": user, "c": cat, "e": datetime.fromisoformat(effective).date()},
        )
        return bid

    with pytest.raises(IntegrityError):
        async with conn.begin_nested():
            await insert("2026-10-15")
    first = await insert("2026-10-01")
    with pytest.raises(IntegrityError):
        async with conn.begin_nested():
            await insert("2026-10-01")
    await conn.execute(text("UPDATE budgets SET deleted_at = now() WHERE id=:i"), {"i": first})
    await insert("2026-10-01")


async def test_regla_recurrente_fin_por_fecha_o_por_conteo_no_ambos(conn: AsyncConnection) -> None:
    user = await make_user(conn)
    cat = await make_category(conn, user)

    async def insert(end_on: str | None, max_occ: int | None) -> None:
        await conn.execute(
            text(
                "INSERT INTO recurring_rules (id, user_id, type, amount_minor, category_id, "
                "frequency, "
                "start_on, end_on, max_occurrences, mode, generate_from, created_at) "
                "VALUES (:id, :u, 'expense', 100, :c, 'monthly', '2026-10-05', "
                ":e, :m, 'auto', '2026-10-05', now())"
            ),
            {
                "id": uuid.uuid4(),
                "u": user,
                "c": cat,
                "e": date.fromisoformat(end_on) if end_on else None,
                "m": max_occ,
            },
        )

    with pytest.raises(IntegrityError):
        async with conn.begin_nested():
            await insert("2027-01-01", 3)
    with pytest.raises(IntegrityError):
        async with conn.begin_nested():
            await insert(None, 0)
    await insert("2027-01-01", None)
    await insert(None, 3)
    await insert(None, None)
