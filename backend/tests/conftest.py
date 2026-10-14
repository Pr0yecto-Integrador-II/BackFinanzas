"""
Top-level conftest para la suite completa de pruebas.
Proporciona la configuración de base de datos de pruebas (PostgreSQL en Docker)
y el fixture de sesión migrated_database compartido por integración, seguridad y aceptación.
"""

import asyncio
import os
import subprocess
from collections.abc import Iterator

import asyncpg  # type: ignore[import-untyped]
import pytest

ADMIN_DSN = "postgresql://finanzas:finanzas@localhost:5433/postgres"
TEST_DB = "finanzas_test"
TEST_URL = f"postgresql+asyncpg://finanzas:finanzas@localhost:5433/{TEST_DB}"


async def _recreate_database() -> None:
    conn = await asyncpg.connect(ADMIN_DSN)
    try:
        await conn.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
        await conn.execute(f"CREATE DATABASE {TEST_DB}")
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def migrated_database() -> Iterator[None]:
    """Crea una BD limpia y le aplica las migraciones reales de Alembic."""
    asyncio.run(_recreate_database())
    env = {**os.environ, "DATABASE_URL": TEST_URL, "JWT_SECRET": "x" * 32}
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
    yield
