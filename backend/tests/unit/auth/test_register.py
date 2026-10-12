import pytest

from app.modules.auth.application.register import RegisterInput
from app.modules.auth.domain.errors import (
    EmailAlreadyRegisteredError,
    InvalidCurrencyError,
    InvalidEmailError,
    PasswordLengthError,
    PasswordMismatchError,
    WeakPasswordError,
)
from tests.unit.auth.fakes import World


def data(**over: str) -> RegisterInput:
    base = {
        "email": "Ana@Correo.com ",
        "password": "clave1234",
        "password_confirmation": "clave1234",
        "currency": "COP",
    }
    return RegisterInput(**{**base, **over})


async def test_registro_exitoso_normaliza_correo_y_deja_sesion_iniciada() -> None:
    w = World()
    session = await w.register.execute(data())
    assert session.user.email == "ana@correo.com"
    assert session.user.currency == "COP"
    assert session.user.password_hash == "hashed:clave1234"  # nunca la contraseña en claro
    assert session.access_token and session.refresh_token
    assert len(w.tokens.active(session.user.id)) == 1
    assert w.uow.commits == 1


async def test_registro_crea_las_categorias_predeterminadas() -> None:
    w = World()
    session = await w.register.execute(data())
    assert w.seeder.seeded == [session.user.id]


async def test_correo_ya_registrado_aunque_cambien_mayusculas() -> None:
    w = World()
    await w.register.execute(data())
    with pytest.raises(EmailAlreadyRegisteredError):
        await w.register.execute(data(email="ANA@correo.com"))
    assert len(w.users.items) == 1


@pytest.mark.parametrize(
    ("over", "error"),
    [
        ({"password": "abcdefgh", "password_confirmation": "abcdefgh"}, WeakPasswordError),
        ({"password": "12345678", "password_confirmation": "12345678"}, WeakPasswordError),
        ({"password": "a1", "password_confirmation": "a1"}, PasswordLengthError),
        ({"password": "a1" * 65, "password_confirmation": "a1" * 65}, PasswordLengthError),
        ({"password_confirmation": "otra1234"}, PasswordMismatchError),
        ({"email": "sin-arroba"}, InvalidEmailError),
        ({"currency": "XXX"}, InvalidCurrencyError),
    ],
)
async def test_validaciones_rechazan_y_no_crean_cuenta(over: dict[str, str], error: type) -> None:
    w = World()
    with pytest.raises(error):
        await w.register.execute(data(**over))
    assert not w.users.items and w.uow.commits == 0


async def test_contrasena_de_128_caracteres_es_valida() -> None:
    w = World()
    pw = "a1" * 64
    await w.register.execute(data(password=pw, password_confirmation=pw))


async def test_moneda_por_defecto_cop_y_acepta_otras() -> None:
    w = World()
    s = await w.register.execute(data(currency="usd"))
    assert s.user.currency == "USD"
