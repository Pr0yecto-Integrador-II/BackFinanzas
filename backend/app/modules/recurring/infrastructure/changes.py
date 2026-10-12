from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recurring.infrastructure.models import RecurringRuleModel
from app.shared.changes import ModelChangesSource


def rule_changes(session: AsyncSession) -> ModelChangesSource:
    return ModelChangesSource(
        session,
        "recurring_rule",
        RecurringRuleModel,
        (
            "type", "amount_minor", "category_id", "description", "frequency", "start_on",
            "end_on", "max_occurrences", "mode", "generate_from", "paused_at", "created_at",
        ),
    )  # fmt: skip
