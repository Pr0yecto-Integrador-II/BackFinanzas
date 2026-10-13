from app.shared.errors import DomainError, TooManyRequestsError, UnauthorizedError


class InvalidEmailError(DomainError):
    message = "Ingresa un correo válido."


class WeakPasswordError(DomainError):
    message = "La contraseña debe tener al menos una letra y un número."


class PasswordLengthError(DomainError):
    message = "La contraseña debe tener entre 8 y 128 caracteres."


class PasswordMismatchError(DomainError):
    message = "Las contraseñas no coinciden."


class InvalidCurrencyError(DomainError):
    message = "La moneda no es válida."


class EmailAlreadyRegisteredError(DomainError):
    message = "Ya existe una cuenta con este correo."


class InvalidResetTokenError(DomainError):
    message = "Este enlace ya no es válido."


class InvalidCredentialsError(UnauthorizedError):
    message = "Correo o contraseña incorrectos."


class InvalidSessionError(UnauthorizedError):
    message = "Tu sesión no es válida. Inicia sesión de nuevo."


class TooManyLoginAttemptsError(TooManyRequestsError):
    message = "Demasiados intentos. Intenta de nuevo en 15 minutos."
