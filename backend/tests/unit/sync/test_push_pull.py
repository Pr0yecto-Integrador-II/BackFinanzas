import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.modules.sync.application.pull import PullChanges
from app.modules.sync.application.push import Change, PushChanges
from app.modules.sync.domain.errors import InvalidChangeError
from app.shared.changes import PulledChange


class Handler:
    def __init__(self, log: list[str], name: str) -> None:
        self.log, self.name = log, name

    async def upsert(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        if data.get("bad"):
            raise InvalidChangeError
        self.log.append(f"upsert:{self.name}")

    async def delete(self, user_id: uuid.UUID, change_id: uuid.UUID, data: dict[str, Any]) -> None:
        self.log.append(f"delete:{self.name}")


class Savepoint:
    def __init__(self) -> None:
        self.opened = 0

    @asynccontextmanager
    async def scope(self) -> AsyncIterator[None]:
        self.opened += 1
        yield


class Lock:
    def __init__(self) -> None:
        self.users: list[uuid.UUID] = []

    async def acquire(self, user_id: uuid.UUID) -> None:
        self.users.append(user_id)


class Source:
    def __init__(self, entity: str, versions: list[int]) -> None:
        self.entity, self.versions = entity, versions

    async def since(self, user_id: uuid.UUID, since: int, limit: int) -> list[PulledChange]:
        return [
            PulledChange(self.entity, uuid.uuid4(), v, {}, False)
            for v in self.versions
            if v > since
        ][:limit]

    async def max_version(self, user_id: uuid.UUID) -> int:
        return max(self.versions, default=0)


class Uow:
    commits = 0

    async def commit(self) -> None:
        self.commits += 1


def _push() -> tuple[PushChanges, list[str], Savepoint, Lock, Uow]:
    log: list[str] = []
    names = ("category", "recurring_rule", "transaction", "budget")
    sp, lock, uow = Savepoint(), Lock(), Uow()
    handlers = {n: Handler(log, n) for n in names}
    push = PushChanges(
        handlers,  # type: ignore[arg-type]
        sp,
        lock,
        [Source("category", [3, 9]), Source("budget", [12])],
        uow,
    )
    return push, log, sp, lock, uow


def _c(entity: str, op: str = "upsert", **data: Any) -> Change:
    return Change(entity, op, uuid.uuid4(), data)


async def test_upserts_en_orden_de_dependencia_y_borrados_al_final_en_orden_inverso() -> None:
    push, log, *_ = _push()
    await push.execute(
        uuid.uuid4(),
        [
            _c("budget"),
            _c("category", "delete"),
            _c("transaction"),
            _c("transaction", "delete"),
            _c("category"),
            _c("recurring_rule"),
        ],
    )
    assert log == [
        "upsert:category", "upsert:recurring_rule", "upsert:transaction", "upsert:budget",
        "delete:transaction", "delete:category",
    ]  # fmt: skip


async def test_un_cambio_invalido_se_rechaza_sin_tumbar_el_lote() -> None:
    push, log, sp, *_ = _push()
    bad, good = _c("transaction", bad=True), _c("category")
    result = await push.execute(uuid.uuid4(), [bad, good])
    assert result.applied == [good.id]
    assert [(r.id, r.code) for r in result.rejected] == [(bad.id, "InvalidChangeError")]
    assert sp.opened == 2 and log == ["upsert:category"]


async def test_bloquea_al_usuario_confirma_y_devuelve_la_version_maxima() -> None:
    push, _, _, lock, uow = _push()
    user = uuid.uuid4()
    result = await push.execute(user, [])
    assert lock.users == [user] and uow.commits == 1 and result.version == 12


async def test_pull_mezcla_por_version_y_pagina() -> None:
    pull = PullChanges([Source("category", [1, 4, 7]), Source("transaction", [2, 3, 9])])
    first = await pull.execute(uuid.uuid4(), 0, 4)
    assert [c.version for c in first.changes] == [1, 2, 3, 4]
    assert first.next_since == 4 and first.has_more is True
    last = await pull.execute(uuid.uuid4(), 4, 4)
    assert [c.version for c in last.changes] == [7, 9] and last.has_more is False


async def test_pull_sin_novedades_conserva_since() -> None:
    result = await PullChanges([Source("category", [1])]).execute(uuid.uuid4(), 5, 10)
    assert (result.changes, result.next_since, result.has_more) == ([], 5, False)
