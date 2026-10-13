from app.shared.errors import DomainError


class InvalidTypeError(DomainError):
    message = "El tipo de movimiento no es válido."


class InvalidAmountError(DomainError):
    message = "Ingresa un monto mayor que 0 y de hasta 13 dígitos."


class DescriptionTooLongError(DomainError):
    message = "La descripción admite hasta 100 caracteres."


class InvalidFrequencyError(DomainError):
    message = "La frecuencia no es válida."


class InvalidModeError(DomainError):
    message = "El modo debe ser automático o con confirmación."


class EndConflictError(DomainError):
    message = "El fin es por fecha o por número de repeticiones, no por ambos."


class InvalidMaxOccurrencesError(DomainError):
    message = "El número de repeticiones debe ser mayor que 0."


class EndBeforeStartError(DomainError):
    message = "La fecha de fin no puede ser anterior a la de inicio."


class GenerateFromBeforeStartError(DomainError):
    message = "La fecha desde la que se genera no puede ser anterior al inicio."


class GenerateFromMovedBackError(DomainError):
    message = (
        "No se puede retroceder la fecha desde la que se genera: se repetirían fechas ya omitidas."
    )


class InvalidCategoryError(DomainError):
    message = "Elige una categoría válida."


class CategoryTypeMismatchError(DomainError):
    def __init__(self, type_: str) -> None:
        kind = "gasto" if type_ == "expense" else "ingreso"
        super().__init__(f"La categoría debe ser de tipo {kind}.")


class RuleNotFoundError(DomainError):
    message = "La regla recurrente no existe."
