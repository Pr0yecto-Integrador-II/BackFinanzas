"""Punto único donde se conectan los módulos entre sí (D-03).

Aquí es el único lugar que conoce a la vez a `categories` y a los módulos que guardan
`category_id`. Ningún módulo importa la infraestructura de otro.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budgets.application.delete import DeleteBudget
from app.modules.budgets.application.upsert import UpsertBudget
from app.modules.budgets.infrastructure.category_lookup import (
    CategoriesLookup as BudgetCategoriesLookup,
)
from app.modules.budgets.infrastructure.category_referrer import BudgetCategoryReferrer
from app.modules.budgets.infrastructure.changes import budget_changes
from app.modules.budgets.infrastructure.repository import SqlBudgetRepository
from app.modules.categories.application.create_defaults import CreateDefaultCategories
from app.modules.categories.application.delete import DeleteCategory
from app.modules.categories.application.get_active import GetActiveCategory
from app.modules.categories.application.ports import CategoryReferrer
from app.modules.categories.application.upsert import UpsertCategory
from app.modules.categories.infrastructure.changes import category_changes
from app.modules.categories.infrastructure.repository import SqlCategoryRepository
from app.modules.recurring.application.delete import DeleteRule
from app.modules.recurring.application.upsert import UpsertRule
from app.modules.recurring.infrastructure.category_lookup import (
    CategoriesLookup as RecurringCategoriesLookup,
)
from app.modules.recurring.infrastructure.category_referrer import RecurringCategoryReferrer
from app.modules.recurring.infrastructure.changes import rule_changes
from app.modules.recurring.infrastructure.repository import SqlRecurringRuleRepository
from app.modules.recurring.infrastructure.rule_lookup import SqlRecurringRuleLookup
from app.modules.sync.application.ports import ChangesSource
from app.modules.sync.application.pull import PullChanges
from app.modules.sync.application.push import PushChanges
from app.modules.sync.infrastructure.handlers import (
    BudgetHandler,
    CategoryHandler,
    RuleHandler,
    TransactionHandler,
)
from app.modules.sync.infrastructure.sql import AdvisoryUserLock, SqlSavepoint
from app.modules.transactions.application.delete import DeleteTransaction
from app.modules.transactions.application.upsert import UpsertTransaction
from app.modules.transactions.infrastructure.category_lookup import CategoriesLookup
from app.modules.transactions.infrastructure.category_referrer import (
    TransactionCategoryReferrer,
)
from app.modules.transactions.infrastructure.changes import transaction_changes
from app.modules.transactions.infrastructure.pending_occurrences import SqlPendingOccurrences
from app.modules.transactions.infrastructure.repository import SqlTransactionRepository
from app.shared.clock import Clock
from app.shared.sql_uow import SqlAlchemyUnitOfWork


def category_referrers(session: AsyncSession) -> list[CategoryReferrer]:
    return [
        TransactionCategoryReferrer(session),
        RecurringCategoryReferrer(session),
        BudgetCategoryReferrer(session),
    ]


def create_default_categories(session: AsyncSession, clock: Clock) -> CreateDefaultCategories:
    return CreateDefaultCategories(SqlCategoryRepository(session), clock)


def upsert_category(session: AsyncSession) -> UpsertCategory:
    return UpsertCategory(SqlCategoryRepository(session), category_referrers(session))


def delete_category(session: AsyncSession, clock: Clock) -> DeleteCategory:
    return DeleteCategory(SqlCategoryRepository(session), category_referrers(session), clock)


def upsert_transaction(session: AsyncSession, clock: Clock) -> UpsertTransaction:
    return UpsertTransaction(
        SqlTransactionRepository(session),
        CategoriesLookup(GetActiveCategory(SqlCategoryRepository(session))),
        SqlRecurringRuleLookup(session),
        clock,
    )


def delete_transaction(session: AsyncSession, clock: Clock) -> DeleteTransaction:
    return DeleteTransaction(SqlTransactionRepository(session), clock)


def upsert_rule(session: AsyncSession) -> UpsertRule:
    return UpsertRule(
        SqlRecurringRuleRepository(session),
        RecurringCategoriesLookup(GetActiveCategory(SqlCategoryRepository(session))),
    )


def delete_rule(session: AsyncSession, clock: Clock) -> DeleteRule:
    return DeleteRule(SqlRecurringRuleRepository(session), SqlPendingOccurrences(session), clock)


def upsert_budget(session: AsyncSession) -> UpsertBudget:
    return UpsertBudget(
        SqlBudgetRepository(session),
        BudgetCategoriesLookup(GetActiveCategory(SqlCategoryRepository(session))),
    )


def delete_budget(session: AsyncSession, clock: Clock) -> DeleteBudget:
    return DeleteBudget(SqlBudgetRepository(session), clock)


def _change_sources(session: AsyncSession) -> list[ChangesSource]:
    return [
        category_changes(session),
        rule_changes(session),
        transaction_changes(session),
        budget_changes(session),
    ]


def push_changes(session: AsyncSession, clock: Clock) -> PushChanges:
    handlers = {
        "category": CategoryHandler(upsert_category(session), delete_category(session, clock)),
        "recurring_rule": RuleHandler(upsert_rule(session), delete_rule(session, clock)),
        "transaction": TransactionHandler(
            upsert_transaction(session, clock), delete_transaction(session, clock)
        ),
        "budget": BudgetHandler(upsert_budget(session), delete_budget(session, clock)),
    }
    return PushChanges(
        handlers,  # type: ignore[arg-type]
        SqlSavepoint(session),
        AdvisoryUserLock(session),
        _change_sources(session),
        SqlAlchemyUnitOfWork(session),
    )


def pull_changes(session: AsyncSession) -> PullChanges:
    return PullChanges(_change_sources(session))
