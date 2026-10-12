import uuid
from typing import Any

from tests.integration.sync.conftest import Env, new_id, register

NOW = "2026-10-01T09:00:00Z"


async def _auth(env: Env, email: str = "ana@correo.com") -> dict[str, str]:
    body = await register(env, email)
    return {"Authorization": f"Bearer {body['access_token']}"}


async def _push(env: Env, headers: dict[str, str], *changes: dict[str, Any]) -> dict[str, Any]:
    res = await env.client.post("/sync/push", json={"changes": list(changes)}, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()  # type: ignore[no-any-return]


async def _pull(
    env: Env, headers: dict[str, str], since: int = 0, limit: int = 500
) -> dict[str, Any]:
    res = await env.client.get(f"/sync/pull?since={since}&limit={limit}", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()  # type: ignore[no-any-return]


def _tx(cat: str, **over: Any) -> dict[str, Any]:
    data = {
        "type": "expense", "amount_minor": 2_500_000, "category_id": cat,
        "occurred_on": "2026-10-01", "created_at": NOW, "tags": ["#Viaje"],
    }  # fmt: skip
    return {"entity": "transaction", "op": "upsert", "id": new_id(), "data": {**data, **over}}


async def _expense_category(env: Env, headers: dict[str, str]) -> str:
    pulled = await _pull(env, headers)
    return str(
        next(
            c["id"]
            for c in pulled["changes"]
            if c["entity"] == "category" and c["data"]["type"] == "expense"
        )
    )


async def test_requiere_autenticacion(env: Env) -> None:
    assert (await env.client.post("/sync/push", json={"changes": []})).status_code == 401
    assert (await env.client.get("/sync/pull")).status_code == 401


async def test_el_registro_deja_las_12_categorias_en_el_primer_pull(env: Env) -> None:
    headers = await _auth(env)
    pulled = await _pull(env, headers)
    assert len(pulled["changes"]) == 12 and pulled["has_more"] is False
    assert pulled["next_since"] == max(c["version"] for c in pulled["changes"])


async def test_push_guarda_el_gasto_y_el_pull_lo_devuelve_con_version_del_servidor(
    env: Env,
) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    since = (await _pull(env, headers))["next_since"]
    change = _tx(cat)
    out = await _push(env, headers, change)
    assert out["applied"] == [change["id"]] and out["rejected"] == []
    news = await _pull(env, headers, since)
    [got] = news["changes"]
    assert got["entity"] == "transaction" and got["id"] == change["id"] and not got["deleted"]
    assert got["data"]["tags"] == ["viaje"] and got["data"]["amount_minor"] == 2_500_000
    assert got["version"] == out["version"] == news["next_since"]


async def test_reenviar_el_mismo_cambio_no_duplica(env: Env) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    change = _tx(cat)
    await _push(env, headers, change)
    again = await _push(env, headers, change)
    assert again["applied"] == [change["id"]]
    txs = [c for c in (await _pull(env, headers))["changes"] if c["entity"] == "transaction"]
    assert len(txs) == 1


async def test_rechazo_por_cambio_no_tumba_el_lote(env: Env) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    future, ok = _tx(cat, occurred_on="2999-01-01"), _tx(cat)
    out = await _push(env, headers, future, ok)
    assert out["applied"] == [ok["id"]]
    assert [(r["id"], r["code"]) for r in out["rejected"]] == [(future["id"], "FutureDateError")]


async def test_datos_extra_o_mal_formados_se_rechazan_por_cambio(env: Env) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    extra = _tx(cat, user_id=str(uuid.uuid4()))
    cents = _tx(cat, amount_minor=25.5)
    out = await _push(env, headers, extra, cents)
    assert out["applied"] == []
    assert {r["code"] for r in out["rejected"]} == {"InvalidChangeError"}
    assert "user_id" in out["rejected"][0]["message"] or "user_id" in out["rejected"][1]["message"]


async def test_lote_de_mas_de_500_cambios_se_rechaza(env: Env) -> None:
    headers = await _auth(env)
    changes = [{"entity": "budget", "op": "delete", "id": new_id()}] * 501
    res = await env.client.post("/sync/push", json={"changes": changes}, headers=headers)
    assert res.status_code == 422


async def test_borrar_categoria_en_uso_reasigna_en_el_mismo_lote(env: Env) -> None:
    headers = await _auth(env)
    pulled = (await _pull(env, headers))["changes"]
    expenses = [c["id"] for c in pulled if c["data"].get("type") == "expense"]
    source, target = expenses[0], expenses[1]
    tx = _tx(source)
    # En un solo lote: el movimiento se crea y luego se borra su categoría con reasignación.
    out = await _push(
        env, headers, tx,
        {"entity": "category", "op": "delete", "id": source, "data": {"reassign_to": target}},
    )  # fmt: skip
    assert out["rejected"] == []
    changes = (await _pull(env, headers))["changes"]
    moved = next(c for c in changes if c["id"] == tx["id"])
    assert moved["data"]["category_id"] == target
    assert next(c for c in changes if c["id"] == source)["deleted"] is True


async def test_borrar_categoria_en_uso_sin_destino_se_rechaza(env: Env) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    await _push(env, headers, _tx(cat))
    out = await _push(env, headers, {"entity": "category", "op": "delete", "id": cat})
    assert [r["code"] for r in out["rejected"]] == ["ReassignmentRequiredError"]


async def test_reglas_y_presupuestos_viajan_por_el_push(env: Env) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    rule = {
        "entity": "recurring_rule", "op": "upsert", "id": new_id(),
        "data": {
            "type": "expense", "amount_minor": 120_000_000, "category_id": cat,
            "frequency": "monthly", "start_on": "2026-10-05", "mode": "confirm",
            "generate_from": "2026-10-05", "created_at": NOW,
        },
    }  # fmt: skip
    budget = {
        "entity": "budget", "op": "upsert", "id": new_id(),
        "data": {
            "category_id": cat, "amount_minor": 60_000_000,
            "effective_from": "2026-10-01", "created_at": NOW,
        },
    }  # fmt: skip
    out = await _push(env, headers, budget, rule)
    assert set(out["applied"]) == {rule["id"], budget["id"]}
    entities = {c["entity"] for c in (await _pull(env, headers))["changes"]}
    assert {"recurring_rule", "budget"} <= entities


async def test_el_pull_pagina(env: Env) -> None:
    headers = await _auth(env)
    first = await _pull(env, headers, 0, 5)
    assert len(first["changes"]) == 5 and first["has_more"] is True
    second = await _pull(env, headers, first["next_since"], 500)
    assert len(second["changes"]) == 7 and second["has_more"] is False


async def test_cada_usuario_solo_ve_y_toca_lo_suyo(env: Env) -> None:
    ana, luis = await _auth(env, "ana@correo.com"), await _auth(env, "luis@correo.com")
    cat_ana = await _expense_category(env, ana)
    change = _tx(cat_ana)
    await _push(env, ana, change)
    # Luis no ve el movimiento de Ana ni puede usar su categoría ni pisar su id.
    assert change["id"] not in {c["id"] for c in (await _pull(env, luis))["changes"]}
    cat_luis = await _expense_category(env, luis)
    robbed = await _push(env, luis, _tx(cat_ana), {**_tx(cat_luis), "id": change["id"]})
    assert robbed["applied"] == [] and len(robbed["rejected"]) == 2
    assert {r["code"] for r in robbed["rejected"]} == {
        "InvalidCategoryError",
        "TransactionNotFoundError",
    }
