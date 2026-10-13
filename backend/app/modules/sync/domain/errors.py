from app.shared.errors import DomainError


class InvalidChangeError(DomainError):
    message = "El cambio tiene datos inválidos."


class StorageConflictError(DomainError):
    message = "El cambio choca con datos existentes."
