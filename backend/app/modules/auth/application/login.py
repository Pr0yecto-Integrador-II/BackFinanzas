from dataclasses import dataclass

from app.modules.auth.application.ports import PasswordHasher, RateLimiter, UserRepository
from app.modules.auth.application.sessions import IssueSession, Session
from app.modules.auth.domain.errors import InvalidCredentialsError, TooManyLoginAttemptsError
from app.modules.auth.domain.rules import normalize_email
from app.shared.errors import DomainError
from app.shared.uow import UnitOfWork

MAX_FAILED_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60


@dataclass(frozen=True)
class LoginInput:
    email: str
    password: str
    ip: str


class LoginUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        limiter: RateLimiter,
        issue_session: IssueSession,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._limiter = limiter
        self._issue_session = issue_session
        self._uow = uow

    async def execute(self, data: LoginInput) -> Session:
        try:
            email = normalize_email(data.email)
        except DomainError:
            raise InvalidCredentialsError from None  # mismo mensaje que cualquier otro fallo
        counter, lock = f"login:fail:{email}:{data.ip}", f"login:lock:{email}:{data.ip}"

        if await self._limiter.has_flag(lock):
            raise TooManyLoginAttemptsError
        user = await self._users.get_by_email(email)
        valid = await self._hasher.verify(data.password, user.password_hash if user else None)
        if user is None or not valid:
            if await self._limiter.incr(counter, WINDOW_SECONDS) >= MAX_FAILED_ATTEMPTS:
                await self._limiter.set_flag(lock, WINDOW_SECONDS)
            raise InvalidCredentialsError

        await self._limiter.reset(counter)
        session = await self._issue_session.execute(user)
        await self._uow.commit()
        return session
