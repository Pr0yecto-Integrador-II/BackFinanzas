from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.clock import SystemClock
from app.shared.errors import DomainError


class FutureDateError(DomainError):
    message = "La fecha no puede ser futura."


def test_domain_error_expone_code_y_message() -> None:
    err = FutureDateError()
    assert err.code == "FutureDateError"
    assert err.message == "La fecha no puede ser futura."


def test_system_clock_devuelve_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is UTC
    assert abs((datetime.now(UTC) - now).total_seconds()) < 5


def test_health() -> None:
    res = TestClient(create_app()).get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_domain_error_se_traduce_a_422() -> None:
    app = create_app()

    @app.get("/boom")
    async def boom() -> None:
        raise FutureDateError

    res = TestClient(app).get("/boom")
    assert res.status_code == 422
    assert res.json() == {"code": "FutureDateError", "message": "La fecha no puede ser futura."}
