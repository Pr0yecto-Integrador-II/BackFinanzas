import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app import composition
from app.modules.categories.application.upsert import UpsertCategoryInput
from tests.conftest import TEST_URL
from tests.unit.auth.fakes import FakeClock


@pytest_asyncio.fixture
async def conn(migrated_database: None) -> AsyncIterator[AsyncConnection]:
    """Conexión dentro de una transacción que siempre se revierte."""
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    async with engine.connect() as connection:
        trans = await connection.begin()
        try:
            yield connection
        finally:
            await trans.rollback()
    await engine.dispose()


async def make_user(conn: AsyncConnection, email: str = "ana@correo.com") -> uuid.UUID:
    row = await conn.execute(
        text("INSERT INTO users (email, password_hash) VALUES (:e, 'hash') RETURNING id"),
        {"e": email},
    )
    user_id: uuid.UUID = row.scalar_one()
    return user_id


async def make_category(
    conn: AsyncConnection, user_id: uuid.UUID, name_key: str = "comida", type_: str = "expense"
) -> uuid.UUID:
    cid = uuid.uuid4()
    await conn.execute(
        text(
            "INSERT INTO categories (id, user_id, name, name_key, type, icon, color, created_at) "
            "VALUES (:id, :u, :n, :n, :t, 'x', '#F97316', :now)"
        ),
        {"id": cid, "u": user_id, "n": name_key, "t": type_, "now": datetime.now(UTC)},
    )
    return cid


@pytest_asyncio.fixture
async def session(conn: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """Sesión dentro de la transacción de prueba, que se revierte al terminar."""
    async with AsyncSession(
        bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
    ) as s:
        yield s


class Db:
    """Atajos para sembrar y consultar datos con SQL directo."""

    def __init__(self, session: AsyncSession) -> None:
        self.s = session
        self.clock = FakeClock()
        self.upsert = composition.upsert_category(session)
        self.delete = composition.delete_category(session, self.clock)

    async def user(self, email: str = "ana@correo.com") -> uuid.UUID:
        return await make_user(await self.s.connection(), email)

    async def category(self, user: uuid.UUID, name: str, type_: str = "expense") -> uuid.UUID:
        cid = uuid.uuid4()
        await self.upsert.execute(
            user,
            UpsertCategoryInput(
                cid, name, type_, "pets", "#F97316", datetime(2026, 10, 1, tzinfo=UTC)
            ),
        )
        await self.s.flush()
        return cid

    async def tx(self, user: uuid.UUID, cat: uuid.UUID, deleted: bool = False) -> uuid.UUID:
        tid = uuid.uuid4()
        await self.s.execute(
            text(
                "INSERT INTO transactions (id, user_id, type, amount_minor, category_id, "
                "occurred_on, created_at, deleted_at) VALUES (:id, :u, 'expense', 100, :c, "
                "'2026-10-01', now(), CASE WHEN :d THEN now() END)"
            ),
            {"id": tid, "u": user, "c": cat, "d": deleted},
        )
        return tid

    async def rule(self, user: uuid.UUID, cat: uuid.UUID) -> uuid.UUID:
        rid = uuid.uuid4()
        await self.s.execute(
            text(
                "INSERT INTO recurring_rules (id, user_id, type, amount_minor, category_id, "
                "frequency, start_on, mode, generate_from, created_at) VALUES (:id, :u, "
                "'expense', 100, :c, 'monthly', '2026-10-05', 'auto', '2026-10-05', now())"
            ),
            {"id": rid, "u": user, "c": cat},
        )
        return rid

    async def budget(self, user: uuid.UUID, cat: uuid.UUID, amount: int = 600000) -> uuid.UUID:
        bid = uuid.uuid4()
        await self.s.execute(
            text(
                "INSERT INTO budgets (id, user_id, category_id, amount_minor, effective_from, "
                "created_at) VALUES (:id, :u, :c, :a, '2026-10-01', now())"
            ),
            {"id": bid, "u": user, "c": cat, "a": amount},
        )
        return bid

    async def row(self, table: str, row_id: uuid.UUID) -> dict[str, object]:
        res = await self.s.execute(text(f"SELECT * FROM {table} WHERE id = :i"), {"i": row_id})
        return dict(res.mappings().one())


@pytest_asyncio.fixture
async def db(session: AsyncSession) -> Db:
    return Db(session)
