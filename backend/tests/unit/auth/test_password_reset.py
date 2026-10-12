from datetime import timedelta

import pytest

from app.modules.auth.application.login import LoginInput
from app.modules.auth.application.password_reset import ResetPasswordInput
from app.modules.auth.application.register import RegisterInput
from app.modules.auth.domain.errors import (
    InvalidCredentialsError,
    InvalidResetTokenError,
    InvalidSessionError,
    PasswordMismatchError,
    WeakPasswordError,
)
from tests.unit.auth.fakes import World


async def registered() -> World:
    w = World()
    await w.register.execute(RegisterInput("ana@correo.com", "clave1234", "clave1234"))
    return w


def reset_input(token: str, pw: str = "nueva1234") -> ResetPasswordInput:
    return ResetPasswordInput(token, pw, pw)


async def test_solicitud_envia_correo_con_token_valido_30_minutos() -> None:
    w = await registered()
    await w.request_reset.execute("Ana@correo.com")
    assert [e for e, _ in w.mailer.sent] == ["ana@correo.com"]
    stored = w.resets.items[0]
    assert stored["expires_at"] == w.clock.now() + timedelta(minutes=30)
    assert stored["hash"] != w.mailer.sent[0][1]  # en la base solo el hash


async def test_correo_inexistente_o_invalido_no_envia_nada_y_no_falla() -> None:
    w = await registered()
    await w.request_reset.execute("nadie@correo.com")
    await w.request_reset.execute("basura")
    assert w.mailer.sent == []


async def test_maximo_3_solicitudes_por_hora_sin_revelar_el_limite() -> None:
    w = await registered()
    for _ in range(5):
        await w.request_reset.execute("ana@correo.com")  # ninguna lanza error
    assert len(w.mailer.sent) == 3


async def test_pedir_uno_nuevo_invalida_los_anteriores() -> None:
    w = await registered()
    await w.request_reset.execute("ana@correo.com")
    await w.request_reset.execute("ana@correo.com")
    first, second = (t for _, t in w.mailer.sent)
    with pytest.raises(InvalidResetTokenError):
        await w.reset.execute(reset_input(first))
    await w.reset.execute(reset_input(second))


async def test_restablecer_cambia_la_clave_y_cierra_todas_las_sesiones() -> None:
    w = await registered()
    s = await w.login.execute(LoginInput("ana@correo.com", "clave1234", "1.1.1.1"))
    await w.request_reset.execute("ana@correo.com")
    await w.reset.execute(reset_input(w.mailer.sent[0][1]))

    assert w.tokens.active(s.user.id) == []
    with pytest.raises(InvalidSessionError):
        await w.refresh.execute(s.refresh_token)
    with pytest.raises(InvalidCredentialsError):
        await w.login.execute(LoginInput("ana@correo.com", "clave1234", "1.1.1.1"))
    await w.login.execute(LoginInput("ana@correo.com", "nueva1234", "1.1.1.1"))


async def test_el_enlace_sirve_una_sola_vez() -> None:
    w = await registered()
    await w.request_reset.execute("ana@correo.com")
    token = w.mailer.sent[0][1]
    await w.reset.execute(reset_input(token))
    with pytest.raises(InvalidResetTokenError):
        await w.reset.execute(reset_input(token, "otra12345"))


async def test_enlace_vencido_a_los_30_minutos() -> None:
    w = await registered()
    await w.request_reset.execute("ana@correo.com")
    w.clock.advance(minutes=30, seconds=1)
    with pytest.raises(InvalidResetTokenError) as e:
        await w.reset.execute(reset_input(w.mailer.sent[0][1]))
    assert e.value.message == "Este enlace ya no es válido."


async def test_token_desconocido() -> None:
    with pytest.raises(InvalidResetTokenError):
        await (await registered()).reset.execute(reset_input("inventado"))


async def test_la_nueva_clave_cumple_las_reglas_y_no_consume_el_enlace() -> None:
    w = await registered()
    await w.request_reset.execute("ana@correo.com")
    token = w.mailer.sent[0][1]
    with pytest.raises(WeakPasswordError):
        await w.reset.execute(reset_input(token, "sololetras"))
    with pytest.raises(PasswordMismatchError):
        await w.reset.execute(ResetPasswordInput(token, "nueva1234", "distinta1"))
    await w.reset.execute(reset_input(token))  # el enlace seguía vigente
