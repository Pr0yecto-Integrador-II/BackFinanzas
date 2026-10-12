import uuid
from dataclasses import dataclass

from app.modules.auth.application.ports import (
    DefaultCategoriesSeeder,
    PasswordHasher,
    UserRepository,
)
from app.modules.auth.application.sessions import IssueSession, Session
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.errors import EmailAlreadyRegisteredError
from app.modules.auth.domain.rules import normalize_email, validate_currency, validate_password
from app.shared.uow import UnitOfWork


@dataclass(frozen=True)
class RegisterInput:
    email: str
    password: str
    password_confirmation: str
    currency: str = "COP"


class RegisterUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        seeder: DefaultCategoriesSeeder,
        issue_session: IssueSession,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._seeder = seeder
        self._issue_session = issue_session
        self._uow = uow

    async def execute(self, data: RegisterInput) -> Session:
        email = normalize_email(data.email)
        validate_password(data.password, data.password_confirmation)
        currency = validate_currency(data.currency)
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError
        user = User(uuid.uuid4(), email, await self._hasher.hash(data.password), currency)
        await self._users.add(user)
        await self._seeder.seed(user.id)
        session = await self._issue_session.execute(user)
        await self._uow.commit()  # usuario, categorías y sesión: todo o nada
        return session
