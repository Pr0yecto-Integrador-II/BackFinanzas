"""Worker de ARQ. Se lanza con: `uv run arq app.worker.WorkerSettings`."""

from typing import Any

from arq.connections import RedisSettings

from app.config import get_settings
from app.modules.auth.infrastructure.mailer import LogEmailSender, send_password_reset_email


async def startup(ctx: dict[str, Any]) -> None:
    if get_settings().cookie_secure:
        # Producción: el adaptador de desarrollo escribiría enlaces de recuperación en el log.
        raise RuntimeError("Falta configurar el proveedor de correo real (D-09).")
    ctx["email_sender"] = LogEmailSender()  # D-09: aquí se cambia por el proveedor real


class WorkerSettings:
    functions = [send_password_reset_email]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
