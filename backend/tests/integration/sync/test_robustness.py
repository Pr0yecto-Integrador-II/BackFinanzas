"""Entradas hostiles o raras al push: ningún cambio debe tumbar el lote ni dar 500."""

import uuid
from typing import Any

import pytest

from tests.integration.sync.conftest import Env
from tests.integration.sync.test_sync_api import NOW, _auth, _expense_category, _pull, _push, _tx


def _rule(cat: str, **over: Any) -> dict[str, Any]:
    data = {
        "type": "expense", "amount_minor": 1000, "category_id": cat, "frequency": "monthly",
        "start_on": "2026-10-05", "mode": "confirm", "generate_from": "2026-10-05",
        "created_at": NOW,
    }  # fmt: skip
    return {"entity": "recurring_rule", "op": "upsert", "id": str(uuid.uuid4()),
            "data": {**data, **over}}  # fmt: skip


@pytest.mark.parametrize(
    "over",
    [
        {"description": "hola\x00mundo"},
        {"note": "\x00"},
        {"tags": ["a\x00b"]},
        {"amount_minor": 10**30},
        {"occurred_on": "0001-01-01"},
        {"created_at": "2026-10-01T09:00:00"},  # sin zona horaria
    ],
)
async def test_valores_raros_en_movimientos_se_rechazan_sin_500(
    env: Env, over: dict[str, Any]
) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    bad, good = _tx(cat, **over), _tx(cat)
    out = await _push(env, headers, bad, good)
    assert good["id"] in out["applied"]
    if "occurred_on" not in over:  # una fecha antigua pero válida sí se acepta
        assert [r["id"] for r in out["rejected"]] == [bad["id"]]


@pytest.mark.parametrize(
    "over",
    [
        {"paused_at": "2026-11-01T00:00:00"},  # naive
        {"max_occurrences": 10**12},
        {"description": "\x00"},
    ],
)
async def test_valores_raros_en_reglas_no_tumban_el_lote(env: Env, over: dict[str, Any]) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    bad, good = _rule(cat, **over), _tx(cat)
    out = await _push(env, headers, bad, good)
    assert good["id"] in out["applied"]
    assert [r["id"] for r in out["rejected"]] == [bad["id"]]


async def test_mismo_id_repetido_en_el_lote_no_duplica(env: Env) -> None:
    headers = await _auth(env)
    cat = await _expense_category(env, headers)
    tx = _tx(cat)
    await _push(env, headers, tx, tx, {**tx, "data": {**tx["data"], "amount_minor": 7}})
    txs = [c for c in (await _pull(env, headers))["changes"] if c["entity"] == "transaction"]
    assert len(txs) == 1 and txs[0]["data"]["amount_minor"] == 7


async def test_borrar_y_volver_a_subir_una_categoria_borrada_no_resucita(env: Env) -> None:
    headers = await _auth(env)
    pulled = (await _pull(env, headers))["changes"]
    cat = next(c for c in pulled if c["data"]["type"] == "expense")
    await _push(env, headers, {"entity": "category", "op": "delete", "id": cat["id"]})
    again = await _push(
        env, headers,
        {"entity": "category", "op": "upsert", "id": cat["id"], "data": {
            "name": "Otra", "type": "expense", "icon": "pets", "color": "#F97316",
            "created_at": NOW}},
    )  # fmt: skip
    assert [r["code"] for r in again["rejected"]] == ["CategoryNotFoundError"]
    got = next(c for c in (await _pull(env, headers))["changes"] if c["id"] == cat["id"])
    assert got["deleted"] is True
