import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.modules.auth.api import deps
from tests.integration.auth.conftest import Env, register
from tests.integration.conftest import TEST_URL


async def db_scalar(sql: str, **params: object) -> object:
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    try:
        async with engine.connect() as c:
            return (await c.execute(text(sql), params)).scalar_one()
    finally:
        await engine.dispose()


async def test_registro_devuelve_sesion_y_cookie_segura(env: Env) -> None:
    res = await env.client.post(
        "/auth/register",
        json={
            "email": "Ana@Correo.com ",
            "password": "clave1234",
            "password_confirmation": "clave1234",
            "currency": "COP",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == "ana@correo.com" and body["user"]["currency"] == "COP"
    assert "password" not in res.text and "clave1234" not in res.text

    cookie = res.headers["set-cookie"]
    assert "refresh_token=" in cookie
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/auth" in cookie

    me = await env.client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "ana@correo.com"


async def test_la_clave_se_guarda_con_argon2id_y_el_refresh_solo_como_hash(env: Env) -> None:
    await register(env)
    stored = await db_scalar("SELECT password_hash FROM users")
    assert str(stored).startswith("$argon2id$") and "clave1234" not in str(stored)
    raw = env.client.cookies["refresh_token"]
    assert await db_scalar("SELECT count(*) FROM refresh_tokens WHERE token_hash = :h", h=raw) == 0
    assert len(str(await db_scalar("SELECT token_hash FROM refresh_tokens"))) == 64


async def test_correo_duplicado_y_validaciones_devuelven_422_con_code(env: Env) -> None:
    await register(env)
    dup = await env.client.post(
        "/auth/register",
        json={
            "email": "ANA@correo.com",
            "password": "clave1234",
            "password_confirmation": "clave1234",
        },
    )
    assert dup.status_code == 422 and dup.json()["code"] == "EmailAlreadyRegisteredError"

    weak = await env.client.post(
        "/auth/register",
        json={
            "email": "b@correo.com",
            "password": "abcdefgh",
            "password_confirmation": "abcdefgh",
        },
    )
    assert weak.status_code == 422 and weak.json()["code"] == "WeakPasswordError"
    assert await db_scalar("SELECT count(*) FROM users") == 1


async def test_campos_desconocidos_se_rechazan(env: Env) -> None:
    res = await env.client.post(
        "/auth/register",
        json={
            "email": "a@b.co",
            "password": "clave1234",
            "password_confirmation": "clave1234",
            "id": "forzado",
        },
    )
    assert res.status_code == 422


async def test_el_registro_es_atomico_si_falla_la_creacion_de_categorias(env: Env) -> None:
    class Boom:
        async def seed(self, user_id: object) -> None:
            raise RuntimeError("fallo simulado")

    app = env.client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[deps.get_seeder] = lambda: Boom()
    quiet = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    )
    res = await quiet.post(
        "/auth/register",
        json={"email": "a@b.co", "password": "clave1234", "password_confirmation": "clave1234"},
    )
    assert res.status_code == 500
    assert await db_scalar("SELECT count(*) FROM users") == 0
    assert await db_scalar("SELECT count(*) FROM refresh_tokens") == 0


async def test_login_y_mensaje_unico_de_error(env: Env) -> None:
    await register(env)
    ok = await env.client.post(
        "/auth/login", json={"email": "ANA@correo.com", "password": "clave1234"}
    )
    assert ok.status_code == 200
    bad1 = await env.client.post("/auth/login", json={"email": "ana@correo.com", "password": "x1"})
    bad2 = await env.client.post("/auth/login", json={"email": "no@correo.com", "password": "x1"})
    assert bad1.status_code == bad2.status_code == 401
    assert bad1.json() == bad2.json()
    assert bad1.json()["message"] == "Correo o contraseña incorrectos."


async def test_bloqueo_tras_5_intentos_responde_429(env: Env) -> None:
    await register(env)
    for _ in range(5):
        await env.client.post("/auth/login", json={"email": "ana@correo.com", "password": "x1"})
    res = await env.client.post(
        "/auth/login", json={"email": "ana@correo.com", "password": "clave1234"}
    )
    assert res.status_code == 429
    assert res.json()["message"] == "Demasiados intentos. Intenta de nuevo en 15 minutos."


async def test_refresh_con_cookie_rota_y_el_reuso_cierra_la_familia(env: Env) -> None:
    await register(env)
    old_cookie = env.client.cookies["refresh_token"]
    res = await env.client.post("/auth/refresh")
    assert res.status_code == 200
    new_cookie = env.client.cookies["refresh_token"]
    assert new_cookie != old_cookie

    env.client.cookies.set("refresh_token", old_cookie, path="/auth")  # un atacante reusa el viejo
    assert (await env.client.post("/auth/refresh")).status_code == 401
    env.client.cookies.set("refresh_token", new_cookie, path="/auth")  # y el legítimo ya no sirve
    assert (await env.client.post("/auth/refresh")).status_code == 401


async def test_refresh_solo_viaja_a_las_rutas_de_auth(env: Env) -> None:
    await register(env)
    res = await env.client.get("/health")
    assert "cookie" not in res.request.headers


async def test_refresh_sin_cookie(env: Env) -> None:
    res = await env.client.post("/auth/refresh")
    assert res.status_code == 401 and res.json()["code"] == "InvalidSessionError"


async def test_logout_cierra_la_sesion_y_borra_la_cookie(env: Env) -> None:
    await register(env)
    cookie = env.client.cookies["refresh_token"]
    res = await env.client.post("/auth/logout")
    assert res.status_code == 204
    env.client.cookies.set("refresh_token", cookie, path="/auth")
    assert (await env.client.post("/auth/refresh")).status_code == 401


async def test_logout_all_cierra_las_demas_sesiones(env: Env) -> None:
    await register(env)
    first = env.client.cookies["refresh_token"]
    await env.client.post("/auth/login", json={"email": "ana@correo.com", "password": "clave1234"})
    second = env.client.cookies["refresh_token"]
    assert (await env.client.post("/auth/logout?all=true")).status_code == 204
    for token in (first, second):
        env.client.cookies.set("refresh_token", token, path="/auth")
        assert (await env.client.post("/auth/refresh")).status_code == 401


async def test_me_exige_token_valido(env: Env) -> None:
    assert (await env.client.get("/me")).status_code == 401
    bad = await env.client.get("/me", headers={"Authorization": "Bearer basura"})
    assert bad.status_code == 401


async def test_recuperar_contrasena_flujo_completo(env: Env) -> None:
    await register(env)
    exists = await env.client.post("/auth/password/forgot", json={"email": "ana@correo.com"})
    missing = await env.client.post("/auth/password/forgot", json={"email": "nadie@correo.com"})
    assert exists.status_code == missing.status_code == 200
    assert exists.json() == missing.json()  # no revela si la cuenta existe
    assert len(env.mailer.sent) == 1

    token = env.mailer.sent[0][1]
    old_cookie = env.client.cookies["refresh_token"]
    reset = await env.client.post(
        "/auth/password/reset",
        json={"token": token, "password": "nueva1234", "password_confirmation": "nueva1234"},
    )
    assert reset.status_code == 200

    env.client.cookies.set("refresh_token", old_cookie, path="/auth")
    assert (await env.client.post("/auth/refresh")).status_code == 401  # sesiones cerradas
    old = await env.client.post(
        "/auth/login", json={"email": "ana@correo.com", "password": "clave1234"}
    )
    assert old.status_code == 401
    new = await env.client.post(
        "/auth/login", json={"email": "ana@correo.com", "password": "nueva1234"}
    )
    assert new.status_code == 200

    again = await env.client.post(
        "/auth/password/reset",
        json={"token": token, "password": "otra12345", "password_confirmation": "otra12345"},
    )
    assert again.status_code == 422 and again.json()["message"] == "Este enlace ya no es válido."


async def test_el_registro_crea_las_12_categorias_predeterminadas(env: Env) -> None:
    await register(env)
    assert await db_scalar("SELECT count(*) FROM categories") == 12
    assert await db_scalar("SELECT count(*) FROM categories WHERE type = 'expense'") == 9
    assert await db_scalar("SELECT count(*) FROM categories WHERE type = 'income'") == 3
    assert await db_scalar("SELECT count(*) FROM categories WHERE is_default") == 12
    # categorías de dos usuarios no se mezclan
    await register(env, "luis@correo.com")
    assert await db_scalar("SELECT count(DISTINCT user_id) FROM categories") == 2
