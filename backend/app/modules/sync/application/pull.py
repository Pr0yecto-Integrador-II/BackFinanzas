import uuid
from dataclasses import dataclass

from app.modules.sync.application.ports import ChangesSource
from app.shared.changes import PulledChange


@dataclass(frozen=True)
class PullResult:
    changes: list[PulledChange]
    next_since: int
    has_more: bool


class PullChanges:
    """Entrega lo que cambió después de `since`, mezclando las cuatro tablas por `version`."""

    def __init__(self, sources: list[ChangesSource]) -> None:
        self._sources = sources

    async def execute(self, user_id: uuid.UUID, since: int, limit: int) -> PullResult:
        merged: list[PulledChange] = []
        for source in self._sources:
            merged.extend(await source.since(user_id, since, limit + 1))
        merged.sort(key=lambda c: c.version)
        page = merged[:limit]
        return PullResult(page, page[-1].version if page else since, len(merged) > limit)
