class DomainError(Exception):
    """Error de regla de negocio. La API lo traduce a HTTP 422 con `code` y `message`."""

    message = "Error de validación."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)

    @property
    def code(self) -> str:
        return type(self).__name__


class UnauthorizedError(DomainError):
    """Falta de autenticación válida. La API responde HTTP 401."""


class TooManyRequestsError(DomainError):
    """Se superó un límite de intentos. La API responde HTTP 429."""
