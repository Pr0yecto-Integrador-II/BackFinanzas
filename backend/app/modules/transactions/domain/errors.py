from app.shared.errors import DomainError


class InvalidTypeError(DomainError):
    message = "El tipo de movimiento no es válido."


class InvalidAmountError(DomainError):
    message = "Ingresa un monto mayor que 0 y de hasta 13 dígitos."


class FutureDateError(DomainError):
    message = "La fecha no puede ser futura."


class DescriptionTooLongError(DomainError):
    message = "La descripción admite hasta 100 caracteres."


class NoteTooLongError(DomainError):
    message = "La nota admite hasta 500 caracteres."


class TooManyTagsError(DomainError):
    message = "Máximo 5 etiquetas por movimiento."


class InvalidTagError(DomainError):
    message = "Cada etiqueta debe tener entre 1 y 20 caracteres."


class InvalidStatusError(DomainError):
    message = "El estado del movimiento no es válido."


class PendingWithoutRuleError(DomainError):
    message = "Solo un movimiento recurrente puede quedar pendiente de confirmar."


class InvalidCategoryError(DomainError):
    message = "Elige una categoría válida."


class CategoryTypeMismatchError(DomainError):
    def __init__(self, type_: str) -> None:
        kind = "gasto" if type_ == "expense" else "ingreso"
        super().__init__(f"La categoría debe ser de tipo {kind}.")


class InvalidRecurringRuleError(DomainError):
    message = "La regla recurrente no existe."


class RuleDeletedError(DomainError):
    message = "La regla recurrente fue eliminada: ya no genera movimientos por confirmar."


class TransactionNotFoundError(DomainError):
    message = "El movimiento no existe."


class TransactionTypeLockedError(DomainError):
    message = "El tipo no se puede cambiar. Elimina el movimiento y crea otro."


class RecurrenceLinkLockedError(DomainError):
    message = "El movimiento no puede cambiar de regla recurrente."


class OccurrenceDeletedError(DomainError):
    message = "Esta ocurrencia recurrente fue eliminada u omitida y no se vuelve a generar."
