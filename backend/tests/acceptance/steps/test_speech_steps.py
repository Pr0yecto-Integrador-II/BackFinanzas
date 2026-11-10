"""
Pasos BDD del MVP 2 (servicios de voz): HU16 token, HU17 dictado, HU18 lectura y
HU19 historial. El dictado y la lectura ocurren en FrontFinanzas; aquí se verifica el
contrato del servidor que esas pantallas usan.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.acceptance.conftest import AcceptanceEnv

_FEATURES = Path(__file__).resolve().parent.parent / "features" / "speech"

scenarios(
    str(_FEATURES / "token.feature"),
    str(_FEATURES / "dictado.feature"),
    str(_FEATURES / "lectura.feature"),
    str(_FEATURES / "historial.feature"),
)


def _today() -> str:
    # Código de prueba: el dominio del servidor usa su propio Clock.
    return datetime.now(UTC).date().isoformat()


async def _category_id(env: AcceptanceEnv, name: str) -> str:
    pull = await env.pull()
    cat = next(
        (
            c["id"]
            for c in pull.get("changes", [])
            if c["entity"] == "category" and c["data"]["name"] == name
        ),
        None,
    )
    assert cat is not None, f"No existe la categoría predeterminada {name}"
    return str(cat)


def _dictated(
    env: AcceptanceEnv, type_: str, amount: int, cat: str, **extra: Any
) -> dict[str, Any]:
    """Borrador que FrontFinanzas arma tras interpretar el dictado y que el usuario confirmó."""
    data: dict[str, Any] = {
        "type": type_,
        "amount_minor": amount,
        "category_id": cat,
        "occurred_on": _today(),
        "created_at": datetime.now(UTC).isoformat(),
        "tags": [],
    }
    data.update(extra)
    env.transaction_id = env.new_id()
    return {"entity": "transaction", "op": "upsert", "id": env.transaction_id, "data": data}


async def _transactions(env: AcceptanceEnv) -> list[dict[str, Any]]:
    pull = await env.pull()
    return [c for c in pull.get("changes", []) if c["entity"] == "transaction"]


# ---------------------------------------------------------------------------
# HU16 / HU18 — token de voz
# ---------------------------------------------------------------------------


@given(parsers.parse('que inicié sesión con "{email}"'))
async def sesion_iniciada(env: AcceptanceEnv, email: str) -> None:
    await env.register(email=email)


@given(parsers.parse("ya solicité {n:d} tokens de voz en la última hora"))
async def tokens_previos(env: AcceptanceEnv, n: int) -> None:
    for _ in range(n):
        res = await env.client.post("/speech/token", headers=env.auth_headers())
        assert res.status_code == 200, res.text


@given("el proveedor de voz no responde")
async def proveedor_caido(env: AcceptanceEnv) -> None:
    env.speech.down = True


@when("solicito un token de voz")
async def pedir_token(env: AcceptanceEnv) -> None:
    env.last_response = await env.client.post("/speech/token", headers=env.auth_headers())


@when("solicito un token de voz sin sesión")
async def pedir_token_sin_sesion(env: AcceptanceEnv) -> None:
    env.last_response = await env.client.post("/speech/token")


@when(parsers.parse('solicito un token de voz indicando la voz "{voz}"'))
async def pedir_token_con_voz(env: AcceptanceEnv, voz: str) -> None:
    env.last_response = await env.client.post(
        "/speech/token", json={"voice": voz}, headers=env.auth_headers()
    )


@then(parsers.parse('recibo un token temporal con región "{region}" y vigencia de {s:d} segundos'))
async def token_recibido(env: AcceptanceEnv, region: str, s: int) -> None:
    res = env.last_response
    assert res is not None and res.status_code == 200, res and res.text
    body = res.json()
    assert body["region"] == region and body["expires_in_seconds"] == s and body["token"]
    assert set(body) == {"token", "region", "expires_in_seconds"}  # nunca la clave


@then("la respuesta no se guarda en caché")
async def sin_cache(env: AcceptanceEnv) -> None:
    assert env.last_response is not None
    assert env.last_response.headers["Cache-Control"] == "no-store"


@then(parsers.parse('la respuesta de voz es {status:d} con código "{code}"'))
async def respuesta_con_codigo(env: AcceptanceEnv, status: int, code: str) -> None:
    res = env.last_response
    assert res is not None and res.status_code == status, res and res.text
    assert res.json()["code"] == code


@then(parsers.parse("la respuesta de voz es {status:d}"))
async def respuesta_status(env: AcceptanceEnv, status: int) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code == status


@then(parsers.parse('el mensaje de voz es "{message}"'))
async def mensaje_de_voz(env: AcceptanceEnv, message: str) -> None:
    assert env.last_response is not None
    assert env.last_response.json()["message"] == message


# ---------------------------------------------------------------------------
# HU17 — movimientos dictados y confirmados
# ---------------------------------------------------------------------------


@when('sincronizo el gasto dictado "Gasté veinticinco mil pesos en almuerzo en Alimentación"')
async def gasto_dictado(env: AcceptanceEnv) -> None:
    cat = await _category_id(env, "Alimentación")
    result = await env.push(_dictated(env, "expense", 2_500_000, cat, description="Almuerzo"))
    assert result["applied"] == [env.transaction_id]


@when('sincronizo el ingreso dictado "Recibí tres millones quinientos mil pesos de Salario"')
async def ingreso_dictado(env: AcceptanceEnv) -> None:
    cat = await _category_id(env, "Salario")
    result = await env.push(_dictated(env, "income", 350_000_000, cat))
    assert result["applied"] == [env.transaction_id]


@when(parsers.parse('sincronizo un gasto dictado en "{categoria}" con monto {monto:d}'))
async def gasto_dictado_monto(env: AcceptanceEnv, categoria: str, monto: int) -> None:
    cat = await _category_id(env, categoria)
    env._dictado = await env.push(_dictated(env, "expense", monto, cat))  # type: ignore[attr-defined]


@when(parsers.parse('sincronizo un gasto dictado en "{categoria}" con fecha "{fecha}"'))
async def gasto_dictado_fecha(env: AcceptanceEnv, categoria: str, fecha: str) -> None:
    cat = await _category_id(env, categoria)
    change = _dictated(env, "expense", 1_200_000, cat, occurred_on=fecha)
    env._dictado = await env.push(change)  # type: ignore[attr-defined]


@when(parsers.parse('sincronizo un gasto dictado en la categoría de ingreso "{categoria}"'))
async def gasto_en_categoria_de_ingreso(env: AcceptanceEnv, categoria: str) -> None:
    cat = await _category_id(env, categoria)
    env._dictado = await env.push(_dictated(env, "expense", 1_800_000, cat))  # type: ignore[attr-defined]


@when(parsers.parse('sincronizo dos veces el mismo gasto dictado en "{categoria}"'))
async def doble_guardado(env: AcceptanceEnv, categoria: str) -> None:
    cat = await _category_id(env, categoria)
    change = _dictated(env, "expense", 1_800_000, cat)
    await env.push(change)
    await env.push(change)


@then(
    parsers.parse(
        'el pull trae un gasto de {monto:d} centavos en "{categoria}" '
        'con descripción "{descripcion}"'
    )
)
async def pull_gasto(env: AcceptanceEnv, monto: int, categoria: str, descripcion: str) -> None:
    cat = await _category_id(env, categoria)
    tx = next(c for c in await _transactions(env) if c["id"] == env.transaction_id)
    data = tx["data"]
    assert (data["type"], data["amount_minor"], data["category_id"]) == ("expense", monto, cat)
    assert data["description"] == descripcion
    assert isinstance(data["amount_minor"], int)


@then("el movimiento tiene versión asignada por el servidor")
async def version_servidor(env: AcceptanceEnv) -> None:
    tx = next(c for c in await _transactions(env) if c["id"] == env.transaction_id)
    assert tx["version"] > 0


@then(parsers.parse('el pull trae un ingreso de {monto:d} centavos en "{categoria}"'))
async def pull_ingreso(env: AcceptanceEnv, monto: int, categoria: str) -> None:
    cat = await _category_id(env, categoria)
    tx = next(c for c in await _transactions(env) if c["id"] == env.transaction_id)
    assert (tx["data"]["type"], tx["data"]["amount_minor"]) == ("income", monto)
    assert tx["data"]["category_id"] == cat


@then(parsers.parse('el movimiento dictado es rechazado con código "{code}"'))
async def dictado_rechazado(env: AcceptanceEnv, code: str) -> None:
    result = env._dictado  # type: ignore[attr-defined]
    assert result["applied"] == []
    assert [r["code"] for r in result["rejected"]] == [code]
    assert await _transactions(env) == []  # no se creó nada


@then("solo existe un movimiento dictado")
async def un_solo_movimiento(env: AcceptanceEnv) -> None:
    assert [c["id"] for c in await _transactions(env)] == [env.transaction_id]


# ---------------------------------------------------------------------------
# HU19 — lectura continua del historial
# ---------------------------------------------------------------------------


@when(parsers.parse("renuevo el token de voz {n:d} veces durante la lectura"))
async def renovar_token(env: AcceptanceEnv, n: int) -> None:
    env._renovaciones = [  # type: ignore[attr-defined]
        await env.client.post("/speech/token", headers=env.auth_headers()) for _ in range(n)
    ]


@then("todas las renovaciones de voz son exitosas")
async def renovaciones_ok(env: AcceptanceEnv) -> None:
    codes = [r.status_code for r in env._renovaciones]  # type: ignore[attr-defined]
    assert codes == [200] * len(codes)


@given(parsers.parse('tengo {n:d} gastos sincronizados en "{categoria}"'))
async def gastos_sincronizados(env: AcceptanceEnv, n: int, categoria: str) -> None:
    cat = await _category_id(env, categoria)
    changes = [_dictated(env, "expense", 1_000_000 * (i + 1), cat) for i in range(n)]
    env._ids = [c["id"] for c in changes]  # type: ignore[attr-defined]
    assert len((await env.push(*changes))["applied"]) == n


@when("elimino por sincronización el segundo gasto")
async def eliminar_segundo(env: AcceptanceEnv) -> None:
    deleted = env._ids[1]  # type: ignore[attr-defined]
    await env.push({"entity": "transaction", "op": "delete", "id": deleted})


@then("el pull marca ese gasto como eliminado")
async def marcado_eliminado(env: AcceptanceEnv) -> None:
    by_id = {c["id"]: c for c in await _transactions(env)}
    assert by_id[env._ids[1]]["deleted"] is True  # type: ignore[attr-defined]


@then(parsers.parse("los otros {n:d} gastos siguen vigentes para leer"))
async def vigentes(env: AcceptanceEnv, n: int) -> None:
    ids = env._ids  # type: ignore[attr-defined]
    vivos = [c["id"] for c in await _transactions(env) if not c["deleted"]]
    assert len(vivos) == n
    assert sorted(vivos) == sorted([ids[0], ids[2]])
