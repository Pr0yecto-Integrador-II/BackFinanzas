from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import composition
from app.container import get_clock
from app.modules.auth.api.deps import CurrentUserId
from app.modules.sync.api.schemas import (
    MAX_CHANGES,
    MAX_VERSION,
    PullChangeOut,
    PullOut,
    PushIn,
    PushOut,
    RejectedOut,
)
from app.modules.sync.application.push import Change
from app.shared.clock import Clock
from app.shared.db import get_session

router = APIRouter(prefix="/sync", tags=["sync"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]


@router.post("/push")
async def push(
    body: PushIn, user_id: CurrentUserId, session: SessionDep, clock: ClockDep
) -> PushOut:
    result = await composition.push_changes(session, clock).execute(
        user_id, [Change(c.entity, c.op, c.id, c.data) for c in body.changes]
    )
    return PushOut(
        applied=result.applied,
        rejected=[RejectedOut(id=r.id, code=r.code, message=r.message) for r in result.rejected],
        version=result.version,
    )


@router.get("/pull")
async def pull(
    user_id: CurrentUserId,
    session: SessionDep,
    since: Annotated[int, Query(ge=0, le=MAX_VERSION)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_CHANGES)] = MAX_CHANGES,
) -> PullOut:
    result = await composition.pull_changes(session).execute(user_id, since, limit)
    return PullOut(
        changes=[
            PullChangeOut(
                entity=c.entity, id=c.id, version=c.version, data=c.data, deleted=c.deleted
            )
            for c in result.changes
        ],
        next_since=result.next_since,
        has_more=result.has_more,
    )
