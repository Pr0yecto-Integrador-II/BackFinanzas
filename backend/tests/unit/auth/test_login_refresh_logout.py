from datetime import timedelta

import pytest

from app.modules.auth.application.login import LoginInput
from app.modules.auth.application.register import RegisterInput
from app.modules.auth.domain.errors import (
    InvalidCredentialsError,
    InvalidSessionError,
    TooManyLoginAttemptsError,
)
from tests.unit.auth.fakes import World

IP = "1.2.3.4"


async def registered() -> World:
    w = World()
    await w.register.execute(RegisterInput("ana@correo.com", "clave1234", "clave1234"))
    return w


async def bad_login(w: World, email: str = "ana@correo.com") -> None:
    with pytest.raises(InvalidCredentialsError):
        await w.login.execute(LoginInput(email, "incorrecta1", IP))


async def test_login_exitoso_con_correo_sin_normalizar() -> None:
    w = await registered()
    s = await w.login.execute(LoginInput(" ANA@correo.com", "clave1234", IP))
    assert s.user.email == "ana@correo.com"
    assert len(w.tokens.active(s.user.id)) == 2  # registro + este login


async def test_mensaje_identico_para_correo_inexistente_y_clave_incorrecta() -> None:
    w = await registered()
    with pytest.raises(InvalidCredentialsError) as a:
        await w.login.execute(LoginInput("ana@correo.com", "mala1234", IP))
    with pytest.raises(InvalidCredentialsError) as b:
        await w.login.execute(LoginInput("nadie@correo.com", "mala1234", IP))
    with pytest.raises(InvalidCredentialsError) as c:
        await w.login.execute(LoginInput("no-es-correo", "mala1234", IP))
    assert (
        a.value.message
        == b.value.message
        == c.value.message
        == ("Correo o contraseña incorrectos.")
    )


async def test_correo_inexistente_igual_verifica_un_hash_para_igualar_tiempos() -> None:
    w = await registered()
    await bad_login(w, "nadie@correo.com")
    assert w.hasher.verify_calls_without_hash == 1


async def test_bloqueo_tras_5_fallos_incluso_con_clave_correcta() -> None:
    w = await registered()
    for _ in range(5):
        await bad_login(w)
    with pytest.raises(TooManyLoginAttemptsError) as e:
        await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    assert e.value.message == "Demasiados intentos. Intenta de nuevo en 15 minutos."


async def test_cuatro_fallos_no_bloquean_y_un_exito_reinicia_el_contador() -> None:
    w = await registered()
    for _ in range(4):
        await bad_login(w)
    await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    for _ in range(4):
        await bad_login(w)  # sigue sin bloquear: el contador se reinició


async def test_el_bloqueo_es_por_correo_e_ip() -> None:
    w = await registered()
    for _ in range(5):
        await bad_login(w)
    await w.login.execute(LoginInput("ana@correo.com", "clave1234", "9.9.9.9"))  # otra IP


async def test_refresh_rota_el_token_y_conserva_la_familia() -> None:
    w = await registered()
    s1 = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    s2 = await w.refresh.execute(s1.refresh_token)
    assert s2.refresh_token != s1.refresh_token
    old = await w.tokens.get_by_hash_for_update(w.secure.hash(s1.refresh_token))
    new = await w.tokens.get_by_hash_for_update(w.secure.hash(s2.refresh_token))
    assert old and new and old.revoked_at is not None and new.revoked_at is None
    assert old.family_id == new.family_id


async def test_refresh_renueva_30_dias_desde_el_uso() -> None:
    w = await registered()
    s1 = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    w.clock.advance(days=20)
    s2 = await w.refresh.execute(s1.refresh_token)
    new = await w.tokens.get_by_hash_for_update(w.secure.hash(s2.refresh_token))
    assert new and new.expires_at == w.clock.now() + timedelta(days=30)


async def test_refresh_vencido_se_rechaza() -> None:
    w = await registered()
    s = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    w.clock.advance(days=30, seconds=1)
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(s.refresh_token)


@pytest.mark.parametrize("raw", [None, "", "desconocido"])
async def test_refresh_sin_token_o_desconocido(raw: str | None) -> None:
    with pytest.raises(InvalidSessionError):
        await (await registered()).refresh.execute(raw)


async def test_reusar_un_refresh_viejo_revoca_toda_la_familia() -> None:
    w = await registered()
    s1 = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    s2 = await w.refresh.execute(s1.refresh_token)
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(s1.refresh_token)  # reuso: posible robo
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(s2.refresh_token)  # el legítimo también queda cerrado


async def test_la_revocacion_por_reuso_se_confirma_en_la_base() -> None:
    w = await registered()
    s1 = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    await w.refresh.execute(s1.refresh_token)
    commits = w.uow.commits
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(s1.refresh_token)
    assert w.uow.commits == commits + 1


async def test_logout_cierra_solo_esa_sesion() -> None:
    w = await registered()
    phone = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    pc = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    await w.logout.execute(phone.refresh_token)
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(phone.refresh_token)
    await w.refresh.execute(pc.refresh_token)  # la otra sigue viva


async def test_logout_en_todos_los_dispositivos() -> None:
    w = await registered()
    a = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    b = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    await w.logout.execute(a.refresh_token, everywhere=True)
    assert w.tokens.active(a.user.id) == []
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(b.refresh_token)


@pytest.mark.parametrize("raw", [None, "", "desconocido"])
async def test_logout_es_idempotente(raw: str | None) -> None:
    await (await registered()).logout.execute(raw)


async def test_refresh_de_un_usuario_que_ya_no_existe() -> None:
    w = await registered()
    s = await w.login.execute(LoginInput("ana@correo.com", "clave1234", IP))
    w.users.items.clear()
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(s.refresh_token)


async def test_me_de_un_usuario_inexistente_es_sesion_invalida() -> None:
    import uuid

    from app.modules.auth.application.me import GetMe

    with pytest.raises(InvalidSessionError):
        await GetMe(World().users).execute(uuid.uuid4())
