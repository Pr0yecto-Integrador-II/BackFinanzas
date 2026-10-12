from app.shared.errors import DomainError


class InvalidCategoryNameError(DomainError):
    message = "El nombre debe tener entre 1 y 30 caracteres."


class InvalidCategoryTypeError(DomainError):
    message = "El tipo de categoría no es válido."


class InvalidIconError(DomainError):
    message = "El ícono no es válido."


class InvalidColorError(DomainError):
    message = "El color no es válido."


class CategoryNameTakenError(DomainError):
    def __init__(self, type_: str) -> None:
        kind = "gasto" if type_ == "expense" else "ingreso"
        super().__init__(f"Ya tienes una categoría de {kind} con ese nombre.")


class CategoryNotFoundError(DomainError):
    message = "La categoría no existe."


class CategoryTypeLockedError(DomainError):
    message = "No se puede cambiar el tipo de una categoría que ya se usa."


class LastCategoryOfTypeError(DomainError):
    def __init__(self, type_: str) -> None:
        kind = "gasto" if type_ == "expense" else "ingreso"
        super().__init__(f"Debes tener al menos una categoría de {kind}.")


class ReassignmentRequiredError(DomainError):
    message = "Elige a qué categoría pasar los movimientos antes de eliminarla."


class InvalidReassignmentError(DomainError):
    message = "La categoría de destino debe existir y ser del mismo tipo."
