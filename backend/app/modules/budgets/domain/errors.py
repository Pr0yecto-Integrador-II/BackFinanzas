from app.shared.errors import DomainError


class InvalidAmountError(DomainError):
    message = "Ingresa un monto mayor que 0 y de hasta 13 dígitos."


class InvalidEffectiveFromError(DomainError):
    message = "El presupuesto debe empezar el primer día de un mes."


class InvalidCategoryError(DomainError):
    message = "Elige una categoría válida."


class NotExpenseCategoryError(DomainError):
    message = "Solo las categorías de gasto admiten presupuesto."


class DuplicateBudgetError(DomainError):
    message = "Ya tienes un presupuesto para esa categoría desde ese mes."


class BudgetNotFoundError(DomainError):
    message = "El presupuesto no existe."
