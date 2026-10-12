import os
import subprocess

from tests.integration.conftest import TEST_URL


def test_los_modelos_coinciden_con_las_migraciones(migrated_database: None) -> None:
    """Falla si alguien cambia un modelo sin crear la migración correspondiente."""
    env = {**os.environ, "DATABASE_URL": TEST_URL, "JWT_SECRET": "x" * 32}
    result = subprocess.run(["alembic", "check"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
