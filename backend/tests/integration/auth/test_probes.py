"""Sondeos de entradas raras en auth: nada debe dar 500."""

import pytest

from tests.integration.auth.conftest import Env, register


@pytest.mark.parametrize("path", ["/auth/register", "/auth/login", "/auth/password/forgot",
                                  "/auth/password/reset", "/sync/push"])  # fmt: skip
@pytest.mark.parametrize("body", ["{", "[]", "null", '"x"', "{}"])
async def test_cuerpos_malformados_dan_4xx(env: Env, path: str, body: str) -> None:
    res = await env.client.post(path, content=body, headers={"content-type": "application/json"})
    assert 400 <= res.status_code < 500


async def test_correo_se_normaliza_a_minusculas_en_login(env: Env) -> None:
    await register(env, "Ana@Correo.com")
    res = await env.client.post(
        "/auth/login", json={"email": "ANA@correo.COM", "password": "clave1234"}
    )
    assert res.status_code == 200


async def test_registro_con_nul_o_correo_enorme_no_da_500(env: Env) -> None:
    for email in ["a\x00b@correo.com", "a" * 400 + "@correo.com"]:
        res = await env.client.post(
            "/auth/register",
            json={"email": email, "password": "clave1234", "password_confirmation": "clave1234"},
        )
        assert res.status_code in (401, 422), res.text


async def test_token_manipulado_o_ajeno_da_401(env: Env) -> None:
    body = await register(env)
    token = body["access_token"]
    for bad in [token[:-3] + "abc", "x.y.z", "", token + "a"]:
        res = await env.client.get("/me", headers={"Authorization": f"Bearer {bad}"})
        assert res.status_code == 401
    assert (
        await env.client.get("/me", headers={"Authorization": f"Basic {token}"})
    ).status_code == 401


async def test_pull_con_parametros_invalidos_da_422(env: Env) -> None:
    body = await register(env)
    h = {"Authorization": f"Bearer {body['access_token']}"}
    for q in ["since=-1", "limit=0", "limit=501", "since=abc", f"since={10**30}"]:
        res = await env.client.get(f"/sync/pull?{q}", headers=h)
        assert res.status_code == 422, q
