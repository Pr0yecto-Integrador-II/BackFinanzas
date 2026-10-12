import hashlib
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from app.modules.auth.application.login import LoginUser
from app.modules.auth.application.logout import LogoutUser
from app.modules.auth.application.password_reset import RequestPasswordReset, ResetPassword
from app.modules.auth.application.refresh import RefreshSession
from app.modules.auth.application.register import RegisterUser
from app.modules.auth.application.sessions import IssueSession
from app.modules.auth.domain.entities import RefreshToken, User
from app.modules.auth.domain.errors import EmailAlreadyRegisteredError, InvalidSessionError


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def today(self):  # type: ignore[no-untyped-def]
        return self.current.date()

    def advance(self, **kwargs: float) -> None:
        self.current += timedelta(**kwargs)


class FakeUoW:
    commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeUsers:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, User] = {}

    async def add(self, user: User) -> None:
        if any(u.email == user.email for u in self.items.values()):
            raise EmailAlreadyRegisteredError
        self.items[user.id] = user

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.items.values() if u.email == email), None)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.items.get(user_id)

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> None:
        self.items[user_id] = replace(self.items[user_id], password_hash=password_hash)


class FakeRefreshTokens:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, RefreshToken] = {}

    async def add(self, token: RefreshToken) -> None:
        self.items[token.id] = token

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self.items.values() if t.token_hash == token_hash), None)

    async def revoke(self, token_id: uuid.UUID, at: datetime) -> None:
        self.items[token_id] = replace(self.items[token_id], revoked_at=at)

    async def revoke_family(self, family_id: uuid.UUID, at: datetime) -> None:
        for t in list(self.items.values()):
            if t.family_id == family_id and t.revoked_at is None:
                await self.revoke(t.id, at)

    async def revoke_all_for_user(self, user_id: uuid.UUID, at: datetime) -> None:
        for t in list(self.items.values()):
            if t.user_id == user_id and t.revoked_at is None:
                await self.revoke(t.id, at)

    def active(self, user_id: uuid.UUID) -> list[RefreshToken]:
        return [t for t in self.items.values() if t.user_id == user_id and t.revoked_at is None]


class FakeResets:
    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []

    async def invalidate_unused(self, user_id: uuid.UUID, at: datetime) -> None:
        for r in self.items:
            if r["user_id"] == user_id and r["used_at"] is None:
                r["used_at"] = at

    async def add(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> None:
        self.items.append(
            {"user_id": user_id, "hash": token_hash, "expires_at": expires_at, "used_at": None}
        )

    async def consume(self, token_hash: str, now: datetime) -> uuid.UUID | None:
        for r in self.items:
            if r["hash"] == token_hash and r["used_at"] is None and r["expires_at"] > now:  # type: ignore[operator]
                r["used_at"] = now
                return r["user_id"]  # type: ignore[return-value]
        return None


class FakeHasher:
    def __init__(self) -> None:
        self.verify_calls_without_hash = 0

    async def hash(self, password: str) -> str:
        return f"hashed:{password}"

    async def verify(self, password: str, hashed: str | None) -> bool:
        if hashed is None:
            self.verify_calls_without_hash += 1
            return False
        return hashed == f"hashed:{password}"


class FakeAccess:
    def issue(self, user_id: uuid.UUID) -> str:
        return f"access:{user_id}"

    def decode(self, token: str) -> uuid.UUID:
        if not token.startswith("access:"):
            raise InvalidSessionError
        return uuid.UUID(token.removeprefix("access:"))


class FakeSecure:
    def __init__(self) -> None:
        self.n = 0

    def generate(self) -> str:
        self.n += 1
        return f"raw-{self.n}"

    def hash(self, raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()


class FakeLimiter:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.flags: set[str] = set()

    async def incr(self, key: str, window_seconds: int) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def reset(self, key: str) -> None:
        self.counters.pop(key, None)

    async def set_flag(self, key: str, seconds: int) -> None:
        self.flags.add(key)

    async def has_flag(self, key: str) -> bool:
        return key in self.flags


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, email: str, token: str) -> None:
        self.sent.append((email, token))


class FakeSeeder:
    def __init__(self) -> None:
        self.seeded: list[uuid.UUID] = []

    async def seed(self, user_id: uuid.UUID) -> None:
        self.seeded.append(user_id)


class World:
    """Todos los fakes y los casos de uso ya conectados."""

    def __init__(self) -> None:
        self.clock = FakeClock()
        self.uow = FakeUoW()
        self.users = FakeUsers()
        self.tokens = FakeRefreshTokens()
        self.resets = FakeResets()
        self.hasher = FakeHasher()
        self.secure = FakeSecure()
        self.limiter = FakeLimiter()
        self.mailer = FakeMailer()
        self.seeder = FakeSeeder()
        issue = IssueSession(self.tokens, FakeAccess(), self.secure, self.clock, 30)
        self.register = RegisterUser(self.users, self.hasher, self.seeder, issue, self.uow)
        self.login = LoginUser(self.users, self.hasher, self.limiter, issue, self.uow)
        self.refresh = RefreshSession(
            self.users, self.tokens, self.secure, issue, self.clock, self.uow
        )
        self.logout = LogoutUser(self.tokens, self.secure, self.clock, self.uow)
        self.request_reset = RequestPasswordReset(
            self.users, self.resets, self.secure, self.limiter, self.mailer, self.clock, self.uow
        )
        self.reset = ResetPassword(
            self.users, self.resets, self.tokens, self.hasher, self.secure, self.clock, self.uow
        )
