"""
Pasos BDD para las pruebas de aceptación de autenticación (HU01, HU02, HU03).
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from tests.acceptance.conftest import AcceptanceEnv

_FEATURES = Path(__file__).resolve().parent.parent / "features"

# Asocia todos los escenarios de los .feature de auth
scenarios(
    str(_FEATURES / "auth" / "registro.feature"),
    str(_FEATURES / "auth" / "login.feature"),
    str(_FEATURES / "auth" / "recuperacion.feature"),
)


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------


@given("que no existe ningún usuario registrado")
def sin_usuarios() -> None:
    """El fixture env ya hace TRUNCATE al inicio — nada que hacer."""


@given(parsers.parse('que ya existe una cuenta con correo "{email}"'))
async def cuenta_existente(env: AcceptanceEnv, email: str) -> None:
    await env.register(email=email)


@given(parsers.parse('que existe una cuenta con correo "{email}" y contraseña "{password}"'))
async def cuenta_con_clave(env: AcceptanceEnv, email: str, password: str) -> None:
    await env.register(email=email, password=password)


@given("tengo una sesión activa")
async def sesion_activa(env: AcceptanceEnv) -> None:
    await env.register()


# ---------------------------------------------------------------------------
# Whens — Registro
# ---------------------------------------------------------------------------


@when(parsers.parse('me registro con correo "{email}" y contraseña "{password}"'))
async def cuando_registro(env: AcceptanceEnv, email: str, password: str) -> None:
    await env.register(email=email, password=password)


@when(parsers.parse('me registro con un campo extra "{campo}" con valor "{valor}"'))
async def cuando_registro_campo_extra(env: AcceptanceEnv, campo: str, valor: str) -> None:
    res = await env.client.post(
        "/auth/register",
        json={
            "email": "a@b.co",
            "password": "clave1234",
            "password_confirmation": "clave1234",
            campo: valor,
        },
    )
    env.last_response = res


# ---------------------------------------------------------------------------
# Whens — Login
# ---------------------------------------------------------------------------


@when(parsers.parse('inicio sesión con correo "{email}" y contraseña "{password}"'))
async def cuando_login(env: AcceptanceEnv, email: str, password: str) -> None:
    await env.login(email=email, password=password)


@when(parsers.parse('fallo el login 5 veces con correo "{email}"'))
async def cuando_5_fallos(env: AcceptanceEnv, email: str) -> None:
    for _ in range(5):
        await env.client.post("/auth/login", json={"email": email, "password": "mala"})


@when("intento iniciar sesión con la clave correcta")
async def cuando_login_clave_correcta(env: AcceptanceEnv) -> None:
    await env.login(email="ana@correo.com", password="clave1234")


# ---------------------------------------------------------------------------
# Whens — Recuperación
# ---------------------------------------------------------------------------


@when(parsers.parse('solicito recuperar contraseña con correo "{email}"'))
async def cuando_recuperar(env: AcceptanceEnv, email: str) -> None:
    res = await env.client.post("/auth/password/forgot", json={"email": email})
    env.last_response = res


@when(parsers.parse('restablezco la contraseña con el token recibido a "{nueva}"'))
async def cuando_restablecer(env: AcceptanceEnv, nueva: str) -> None:
    token = env.mailer.sent[-1][1]
    env.reset_token = token
    res = await env.client.post(
        "/auth/password/reset",
        json={"token": token, "password": nueva, "password_confirmation": nueva},
    )
    env.last_response = res


@when("vuelvo a usar el mismo token")
async def cuando_reuso_token(env: AcceptanceEnv) -> None:
    token = env.reset_token
    res = await env.client.post(
        "/auth/password/reset",
        json={"token": token, "password": "otraClave123", "password_confirmation": "otraClave123"},
    )
    env.last_response = res


# ---------------------------------------------------------------------------
# Thens — comunes
# ---------------------------------------------------------------------------


@then("recibo un token de acceso")
def entonces_token(env: AcceptanceEnv) -> None:
    assert env.last_response is not None
    body = env.last_response.json()
    assert "access_token" in body, f"Sin token en: {body}"


@then(parsers.parse('recibo un error con código "{code}"'))
def entonces_error_codigo(env: AcceptanceEnv, code: str) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code in (400, 401, 422, 429), env.last_response.text
    assert env.last_response.json().get("code") == code, env.last_response.json()


@then(parsers.parse('recibo un error 401 con mensaje "{mensaje}"'))
def entonces_error_401(env: AcceptanceEnv, mensaje: str) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code == 401, env.last_response.text
    assert env.last_response.json()["message"] == mensaje


@then(parsers.parse('recibo un error 429 con mensaje "{mensaje}"'))
def entonces_error_429(env: AcceptanceEnv, mensaje: str) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code == 429, env.last_response.text
    assert env.last_response.json()["message"] == mensaje


@then("la respuesta es un error de validación 422")
def entonces_422(env: AcceptanceEnv) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code == 422


@then(parsers.parse('el correo del perfil es "{email}"'))
def entonces_perfil(env: AcceptanceEnv, email: str) -> None:
    assert env.last_response is not None
    assert env.last_response.json()["user"]["email"] == email


@then("se crean 12 categorías por defecto")
async def entonces_12_categorias(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    cats = [c for c in pull.get("changes", []) if c["entity"] == "category"]
    assert len(cats) == 12, f"Se esperaban 12 categorías, llegaron {len(cats)}"


@then("la respuesta incluye una cookie de refresh httpOnly")
def entonces_cookie_httponly(env: AcceptanceEnv) -> None:
    assert env.last_response is not None
    cookie_header = env.last_response.headers.get("set-cookie", "")
    assert "refresh_token=" in cookie_header
    assert "HttpOnly" in cookie_header


@then("la respuesta es exitosa")
def entonces_exitosa(env: AcceptanceEnv) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code == 200, env.last_response.text


@then("se envió un correo de recuperación")
def entonces_correo_enviado(env: AcceptanceEnv) -> None:
    assert len(env.mailer.sent) >= 1, "No se envió ningún correo"


@then("no se envió ningún correo")
def entonces_sin_correo(env: AcceptanceEnv) -> None:
    assert len(env.mailer.sent) == 0, f"Se enviaron {len(env.mailer.sent)} correos inesperadamente"


@then("mi sesión anterior ya no es válida")
async def entonces_sesion_invalida(env: AcceptanceEnv) -> None:
    res = await env.client.post("/auth/refresh")
    assert res.status_code == 401


@then(parsers.parse('puedo iniciar sesión con la nueva contraseña "{password}"'))
async def entonces_login_nueva_clave(env: AcceptanceEnv, password: str) -> None:
    res = await env.login(email="ana@correo.com", password=password)
    assert res.status_code == 200


@then(parsers.parse('recibo un error con mensaje "{mensaje}"'))
def entonces_error_mensaje(env: AcceptanceEnv, mensaje: str) -> None:
    assert env.last_response is not None
    assert env.last_response.json().get("message") == mensaje, env.last_response.json()
