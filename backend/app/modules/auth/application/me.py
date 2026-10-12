import uuid

from app.modules.auth.application.ports import UserRepository
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.errors import InvalidSessionError


class GetMe:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidSessionError
        return user
