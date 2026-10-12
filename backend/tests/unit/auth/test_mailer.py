from typing import Any

from app.modules.auth.infrastructure.mailer import (
    JOB_NAME,
    ArqPasswordResetMailer,
    LogEmailSender,
    send_password_reset_email,
)


class FakePool:
    def __init__(self) -> None:
        self.jobs: list[tuple[Any, ...]] = []

    async def enqueue_job(self, *args: Any) -> None:
        self.jobs.append(args)


async def test_encola_el_envio_con_el_enlace_del_frontend() -> None:
    pool = FakePool()
    await ArqPasswordResetMailer(pool, "https://app.example.com/").send("ana@correo.com", "tok")  # type: ignore[arg-type]
    assert pool.jobs == [
        (JOB_NAME, "ana@correo.com", "https://app.example.com/restablecer?token=tok")
    ]


async def test_el_worker_entrega_el_enlace_al_adaptador_de_correo(caplog: Any) -> None:
    await send_password_reset_email(
        {"email_sender": LogEmailSender()}, "ana@correo.com", "http://x"
    )
    assert "ana@correo.com" in caplog.text
