import logging
from typing import Any

from arq.connections import ArqRedis

log = logging.getLogger(__name__)

JOB_NAME = "send_password_reset_email"


class ArqPasswordResetMailer:
    """Encola el envío en ARQ. El enlace se arma aquí con la URL del frontend."""

    def __init__(self, pool: ArqRedis, frontend_url: str) -> None:
        self._pool = pool
        self._frontend_url = frontend_url.rstrip("/")

    async def send(self, email: str, token: str) -> None:
        await self._pool.enqueue_job(
            JOB_NAME, email, f"{self._frontend_url}/restablecer?token={token}"
        )


class LogEmailSender:
    """Adaptador de desarrollo: escribe el enlace en el log en vez de enviar un correo (D-09)."""

    async def send_password_reset(self, email: str, link: str) -> None:
        log.warning("[DEV] Enlace de recuperación para %s: %s", email, link)


async def send_password_reset_email(ctx: dict[str, Any], email: str, link: str) -> None:
    await ctx["email_sender"].send_password_reset(email, link)
