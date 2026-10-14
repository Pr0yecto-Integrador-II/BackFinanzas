"""
Pasos BDD para pruebas de aceptación de sync: movimientos, categorías y sincronización
(HU04-HU08, HU10 y protocolo de sync).
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from tests.acceptance.conftest import AcceptanceEnv

_FEATURES = Path(__file__).resolve().parent.parent / "features"

scenarios(
    str(_FEATURES / "sync" / "movimientos.feature"),
    str(_FEATURES / "sync" / "categorias.feature"),
    str(_FEATURES / "sync" / "sincronizacion.feature"),
)

NOW = "2026-10-01T09:00:00Z"


# ---------------------------------------------------------------------------
# Givens — contexto de sesión y datos
# ---------------------------------------------------------------------------


@given(parsers.parse('que tengo una sesión activa con "{email}"'))
async def sesion_activa_email(env: AcceptanceEnv, email: str) -> None:
    await env.register(email=email)


@given(parsers.parse('tengo una categoría de tipo "{tipo}"'))
async def categoria_del_tipo(env: AcceptanceEnv, tipo: str) -> None:
    pull = await env.pull()
    cat = next(
        (
            c["id"]
            for c in pull.get("changes", [])
            if c["entity"] == "category" and c["data"]["type"] == tipo
        ),
        None,
    )
    assert cat is not None, f"No se encontró categoría de tipo {tipo}"
    env.category_id = cat


@given(parsers.parse('tengo dos categorías de tipo "{tipo}"'))
async def dos_categorias(env: AcceptanceEnv, tipo: str) -> None:
    pull = await env.pull()
    cats = [
        c["id"]
        for c in pull.get("changes", [])
        if c["entity"] == "category" and c["data"]["type"] == tipo
    ]
    assert len(cats) >= 2, f"Se necesitan al menos 2 categorías de tipo {tipo}"
    env.category_id = cats[0]
    env.category_id_2 = cats[1]


@given("he registrado un gasto con ese movimiento")
async def gasto_registrado(env: AcceptanceEnv) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id)
    await env.push(change)


@given("la primera tiene un movimiento registrado")
async def primera_con_movimiento(env: AcceptanceEnv) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id)
    await env.push(change)


@given("hago un pull inicial y anoto la versión")
async def pull_inicial(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    env.pull_since = pull.get("next_since", 0)


@given(parsers.parse('que existen dos usuarios "{email1}" y "{email2}"'))
async def dos_usuarios(env: AcceptanceEnv, email1: str, email2: str) -> None:
    await env.register(email=email1)
    await env.register(email=email2)


@given("ana tiene una categoría y un movimiento")
async def ana_con_datos(env: AcceptanceEnv) -> None:
    ana_token = env.tokens.get("ana@correo.com")
    pull = await env.pull(token=ana_token)
    cat = next(
        (
            c["id"]
            for c in pull.get("changes", [])
            if c["entity"] == "category" and c["data"]["type"] == "expense"
        ),
        None,
    )
    assert cat
    env.category_id = cat
    change = env.expense_tx(cat)
    env._ana_tx_id = change["id"]  # type: ignore[attr-defined]
    await env.push(change, token=ana_token)


@given('tengo una categoría de tipo "expense" con un movimiento registrado')
async def cat_con_movimiento(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    cat = next(
        (
            c["id"]
            for c in pull.get("changes", [])
            if c["entity"] == "category" and c["data"]["type"] == "expense"
        ),
        None,
    )
    assert cat
    env.category_id = cat
    change = env.expense_tx(cat)
    await env.push(change)


# ---------------------------------------------------------------------------
# Whens — acciones sobre movimientos y sync
# ---------------------------------------------------------------------------


@when(parsers.parse('registro un gasto de {monto:d} centavos en esa categoría con fecha "{fecha}"'))
async def registrar_gasto(env: AcceptanceEnv, monto: int, fecha: str) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id, amount_minor=monto, occurred_on=fecha)
    await env.push(change)


@when(parsers.parse('intento cambiar el tipo del movimiento a "{tipo}"'))
async def cambiar_tipo(env: AcceptanceEnv, tipo: str) -> None:
    assert env.category_id and env.transaction_id
    pull = await env.pull()
    income_cat = next(
        (
            c["id"]
            for c in pull.get("changes", [])
            if c["entity"] == "category" and c["data"]["type"] == tipo
        ),
        None,
    )
    assert income_cat
    change = {
        "entity": "transaction",
        "op": "upsert",
        "id": env.transaction_id,
        "data": {
            "type": tipo,
            "amount_minor": 10_000,
            "category_id": income_cat,
            "occurred_on": "2026-10-01",
            "created_at": NOW,
            "tags": [],
        },
    }
    await env.push(change)


@when(parsers.parse('registro un gasto con fecha "{fecha}"'))
async def gasto_con_fecha(env: AcceptanceEnv, fecha: str) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id, occurred_on=fecha)
    await env.push(change)


@when('registro un gasto con etiquetas "#Viaje" "#viaje" "#Cartagena"')
async def gasto_con_etiquetas(env: AcceptanceEnv) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id, tags=["#Viaje", "#viaje", "#Cartagena"])
    await env.push(change)


@when("borro ese movimiento por sync")
async def borrar_movimiento(env: AcceptanceEnv) -> None:
    assert env.transaction_id
    change = {"entity": "transaction", "op": "delete", "id": env.transaction_id}
    await env.push(change)


@then("borrarlo de nuevo no produce error")
async def borrar_de_nuevo(env: AcceptanceEnv) -> None:
    assert env.transaction_id
    change = {"entity": "transaction", "op": "delete", "id": env.transaction_id}
    result = await env.push(change)
    # Idempotente: puede estar en applied o rejected por not found, ambos son OK
    assert "applied" in result or "rejected" in result


@when("envío un lote con un gasto inválido y uno válido")
async def lote_mixto(env: AcceptanceEnv) -> None:
    assert env.category_id
    invalido = env.expense_tx(env.category_id, occurred_on="2999-01-01")
    env.transaction_id = None  # reset
    valido = env.expense_tx(env.category_id)
    result = await env.push(invalido, valido)
    env._lote_result = result  # type: ignore[attr-defined]


@when("registro el mismo gasto dos veces con el mismo id")
async def mismo_id_dos_veces(env: AcceptanceEnv) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id)
    await env.push(change)
    await env.push(change)


@when("borro esa categoría sin indicar destino")
async def borrar_sin_destino(env: AcceptanceEnv) -> None:
    assert env.category_id
    change = {"entity": "category", "op": "delete", "id": env.category_id}
    await env.push(change)


@when("borro la primera categoría reasignando a la segunda")
async def borrar_reasignando(env: AcceptanceEnv) -> None:
    assert env.category_id and env.category_id_2
    change = {
        "entity": "category",
        "op": "delete",
        "id": env.category_id,
        "data": {"reassign_to": env.category_id_2},
    }
    await env.push(change)


@when("hago el primer pull")
async def primer_pull(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    env._pull_result = pull  # type: ignore[attr-defined]


@when("ana hace pull")
async def ana_hace_pull(env: AcceptanceEnv) -> None:
    ana_token = env.tokens.get("ana@correo.com")
    pull = await env.pull(token=ana_token)
    env._pull_ana = pull  # type: ignore[attr-defined]


@when("registro un nuevo gasto")
async def nuevo_gasto(env: AcceptanceEnv) -> None:
    assert env.category_id
    change = env.expense_tx(env.category_id)
    await env.push(change)


@when("hago pull desde la versión anotada")
async def pull_desde_version(env: AcceptanceEnv) -> None:
    pull = await env.pull(since=env.pull_since)
    env._pull_result = pull  # type: ignore[attr-defined]


@when(parsers.parse("hago pull con límite de {limite:d}"))
async def pull_con_limite(env: AcceptanceEnv, limite: int) -> None:
    pull = await env.pull(limit=limite)
    env._pull_result = pull  # type: ignore[attr-defined]


@when("registro una regla recurrente mensual y un presupuesto por sync")
async def registrar_regla_y_presupuesto(env: AcceptanceEnv) -> None:
    assert env.category_id
    rule = {
        "entity": "recurring_rule",
        "op": "upsert",
        "id": env.new_id(),
        "data": {
            "type": "expense",
            "amount_minor": 120_000_000,
            "category_id": env.category_id,
            "frequency": "monthly",
            "start_on": "2026-10-05",
            "mode": "confirm",
            "generate_from": "2026-10-05",
            "created_at": NOW,
        },
    }
    budget = {
        "entity": "budget",
        "op": "upsert",
        "id": env.new_id(),
        "data": {
            "category_id": env.category_id,
            "amount_minor": 60_000_000,
            "effective_from": "2026-10-01",
            "created_at": NOW,
        },
    }
    await env.push(rule, budget)


@when(parsers.parse("envío un lote de {n:d} cambios"))
async def lote_grande(env: AcceptanceEnv, n: int) -> None:
    changes = [{"entity": "budget", "op": "delete", "id": env.new_id()} for _ in range(n)]
    res = await env.client.post("/sync/push", json={"changes": changes}, headers=env.auth_headers())
    env.last_response = res


@when("luis intenta usar la categoría de ana o pisar el id del movimiento de ana")
async def luis_intenta_robar(env: AcceptanceEnv) -> None:
    luis_token = env.tokens.get("luis@correo.com")
    pull_luis = await env.pull(token=luis_token)
    cat_luis = next(
        (
            c["id"]
            for c in pull_luis.get("changes", [])
            if c["entity"] == "category" and c["data"]["type"] == "expense"
        ),
        None,
    )
    assert cat_luis
    ana_tx_id = getattr(env, "_ana_tx_id", env.transaction_id)
    # Intento 1: usar categoría de ana
    robado1 = env.expense_tx(env.category_id or "")  # cat_ana
    # Intento 2: pisar el id del movimiento de ana
    robado2 = env.expense_tx(cat_luis)
    robado2["id"] = ana_tx_id
    result = await env.push(robado1, robado2, token=luis_token)
    env._robo_result = result  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Thens — verificaciones
# ---------------------------------------------------------------------------


@then("el gasto aparece en el pull con la versión asignada por el servidor")
async def entonces_gasto_en_pull(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    txs = [c for c in pull.get("changes", []) if c["entity"] == "transaction"]
    assert len(txs) >= 1
    assert all("version" in tx for tx in txs)


@then(parsers.parse('el cambio es rechazado con código "{code}"'))
def entonces_rechazado(env: AcceptanceEnv, code: str) -> None:
    last = env.last_response
    assert last is not None
    body = last.json()
    rejected = body.get("rejected", [])
    codes = [r.get("code") for r in rejected]
    assert code in codes, f"Esperaba {code} en rejected, pero llegaron: {codes}"


@then("la respuesta es un error de validación 422")
def respuesta_error_422(env: AcceptanceEnv) -> None:
    assert env.last_response is not None
    assert env.last_response.status_code == 422, (
        f"Esperaba 422, obtuve {env.last_response.status_code}"
    )


@then('las etiquetas guardadas son "viaje" y "cartagena"')
async def entonces_etiquetas(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    txs = [c for c in pull.get("changes", []) if c["entity"] == "transaction"]
    assert len(txs) >= 1
    tags = set(txs[-1]["data"]["tags"])
    assert tags == {"viaje", "cartagena"}, f"Etiquetas inesperadas: {tags}"


@then('el pull lo muestra con "deleted" en true')
async def entonces_deleted_true(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    txs = [c for c in pull.get("changes", []) if c["entity"] == "transaction"]
    assert any(tx.get("deleted") is True for tx in txs)


@then("solo el válido es aceptado")
def entonces_solo_valido(env: AcceptanceEnv) -> None:
    result = getattr(env, "_lote_result", {})
    assert len(result.get("applied", [])) == 1


@then('el inválido aparece en "rejected" con su código de error')
def entonces_invalido_rechazado(env: AcceptanceEnv) -> None:
    result = getattr(env, "_lote_result", {})
    assert len(result.get("rejected", [])) == 1
    assert result["rejected"][0].get("code") == "FutureDateError"


@then("solo existe un movimiento")
async def entonces_un_movimiento(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    txs = [
        c for c in pull.get("changes", []) if c["entity"] == "transaction" and not c.get("deleted")
    ]
    assert len(txs) == 1


@then("recibo exactamente 12 categorías")
def entonces_12_cats(env: AcceptanceEnv) -> None:
    result = getattr(env, "_pull_result", {})
    cats = [c for c in result.get("changes", []) if c["entity"] == "category"]
    assert len(cats) == 12


@then("solo ve sus 12 categorías, no las de luis")
def solo_ve_sus_12(env: AcceptanceEnv) -> None:
    pull = getattr(env, "_pull_ana", {})
    cats = [c for c in pull.get("changes", []) if c["entity"] == "category"]
    assert len(cats) == 12


@then(parsers.parse('9 son de tipo "expense" y 3 de tipo "income"'))
def entonces_tipos_categorias(env: AcceptanceEnv) -> None:
    result = getattr(env, "_pull_result", {})
    cats = [c for c in result.get("changes", []) if c["entity"] == "category"]
    expenses = sum(1 for c in cats if c["data"]["type"] == "expense")
    incomes = sum(1 for c in cats if c["data"]["type"] == "income")
    assert expenses == 9 and incomes == 3


@then("el movimiento ahora pertenece a la segunda categoría")
async def entonces_movimiento_reasignado(env: AcceptanceEnv) -> None:
    assert env.category_id_2 and env.transaction_id
    pull = await env.pull()
    tx = next((c for c in pull["changes"] if c["id"] == env.transaction_id), None)
    assert tx is not None
    assert tx["data"]["category_id"] == env.category_id_2


@then('la primera categoría aparece con "deleted" en true')
async def entonces_cat_deleted(env: AcceptanceEnv) -> None:
    assert env.category_id
    pull = await env.pull()
    cat = next((c for c in pull["changes"] if c["id"] == env.category_id), None)
    assert cat is not None and cat.get("deleted") is True


@then("solo ve sus 12 categorías, no las de luis")
async def entonces_solo_sus_cats(env: AcceptanceEnv) -> None:
    ana_token = env.tokens.get("ana@correo.com")
    pull = await env.pull(token=ana_token)
    cats = [c for c in pull.get("changes", []) if c["entity"] == "category"]
    assert len(cats) == 12


@then("solo recibo el nuevo gasto")
def entonces_solo_nuevo(env: AcceptanceEnv) -> None:
    result = getattr(env, "_pull_result", {})
    txs = [c for c in result.get("changes", []) if c["entity"] == "transaction"]
    assert len(txs) == 1 and not txs[0].get("deleted")


@then(parsers.parse('recibo {n:d} cambios y "has_more" es true'))
def entonces_paginacion(env: AcceptanceEnv, n: int) -> None:
    result = getattr(env, "_pull_result", {})
    assert len(result.get("changes", [])) == n
    assert result.get("has_more") is True


@then('puedo pedir la siguiente página con "next_since"')
async def entonces_siguiente_pagina(env: AcceptanceEnv) -> None:
    result = getattr(env, "_pull_result", {})
    next_since = result.get("next_since", 0)
    segunda = await env.pull(since=next_since)
    assert isinstance(segunda.get("changes"), list)


@then('el pull incluye las entidades "recurring_rule" y "budget"')
async def entonces_incluye_entidades(env: AcceptanceEnv) -> None:
    pull = await env.pull()
    entities = {c["entity"] for c in pull.get("changes", [])}
    assert {"recurring_rule", "budget"} <= entities


@then("ambos intentos son rechazados")
def entonces_ambos_rechazados(env: AcceptanceEnv) -> None:
    result = getattr(env, "_robo_result", {})
    assert result.get("applied") == []
    assert len(result.get("rejected", [])) == 2
