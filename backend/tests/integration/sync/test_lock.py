import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.modules.sync.infrastructure.sql import AdvisoryUserLock
from tests.integration.conftest import TEST_URL


async def test_dos_push_del_mismo_usuario_se_serializan(migrated_database: None) -> None:
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    user = uuid.uuid4()
    try:
        async with maker() as first, maker() as second, maker() as other:
            await AdvisoryUserLock(first).acquire(user)
            # Otro usuario no espera; el mismo usuario sí, hasta que el primero termine.
            await asyncio.wait_for(AdvisoryUserLock(other).acquire(uuid.uuid4()), 2)
            waiting = asyncio.create_task(AdvisoryUserLock(second).acquire(user))
            await asyncio.sleep(0.5)
            assert not waiting.done()
            await first.commit()
            await asyncio.wait_for(waiting, 2)
    finally:
        await engine.dispose()
