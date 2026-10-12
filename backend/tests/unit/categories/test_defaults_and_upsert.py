import uuid

import pytest

from app.modules.categories.domain.catalog import COLORS, DEFAULT_CATEGORIES, ICONS
from app.modules.categories.domain.errors import (
    CategoryNameTakenError,
    CategoryNotFoundError,
    CategoryTypeLockedError,
    InvalidCategoryNameError,
    InvalidCategoryTypeError,
    InvalidColorError,
    InvalidIconError,
)
from app.modules.categories.domain.rules import name_key
from tests.unit.categories.fakes import World


async def test_las_categorias_por_defecto_son_las_12_del_blueprint() -> None:
    w = World()
    await w.defaults.execute(w.user)
    cats = list(w.repo.items.values())
    expenses = [c.name for c in cats if c.type == "expense"]
    incomes = [c.name for c in cats if c.type == "income"]
    assert expenses == [
        "Alimentación", "Transporte", "Vivienda", "Servicios", "Salud", "Educación",
        "Ocio", "Compras", "Otros gastos",
    ]  # fmt: skip
    assert incomes == ["Salario", "Trabajo independiente", "Otros ingresos"]
    assert all(c.is_default and c.user_id == w.user for c in cats)


def test_el_catalogo_por_defecto_usa_solo_iconos_y_colores_permitidos() -> None:
    for _name, _type, icon, color in DEFAULT_CATEGORIES:
        assert icon in ICONS and color in COLORS


@pytest.mark.parametrize(
    ("a", "b"),
    [("Café", "cafe"), ("CAFÉ", "café"), ("  Café ", "cafe"), ("Educación", "educacion")],
)
def test_name_key_ignora_mayusculas_tildes_y_bordes(a: str, b: str) -> None:
    assert name_key(a) == name_key(b)


async def test_crear_categoria() -> None:
    w = World()
    cid = await w.create("Mascotas")
    c = w.repo.items[cid]
    assert (c.name, c.name_key, c.type, c.is_default) == ("Mascotas", "mascotas", "expense", False)


async def test_el_cliente_no_puede_marcar_una_categoria_como_predeterminada() -> None:
    w = World()
    assert not w.repo.items[await w.create("Mascotas")].is_default


async def test_nombre_duplicado_dentro_del_mismo_tipo() -> None:
    w = World()
    await w.create("Café")
    with pytest.raises(CategoryNameTakenError) as e:
        await w.create("cafe")
    assert e.value.message == "Ya tienes una categoría de gasto con ese nombre."


async def test_mismo_nombre_en_otro_tipo_o_en_otro_usuario_si_se_permite() -> None:
    w = World()
    await w.create("Extra", "expense")
    await w.create("Extra", "income")
    await w.create("Extra", "expense", user=uuid.uuid4())


async def test_nombre_de_una_categoria_eliminada_se_puede_reutilizar() -> None:
    w = World()
    old = await w.create("Café")
    await w.create("Otra")
    await w.delete.execute(w.user, old)
    await w.create("Café")


async def test_renombrar_a_si_misma_no_es_duplicado() -> None:
    w = World()
    cid = await w.create("Café")
    await w.upsert.execute(w.user, w.input(cid, "CAFÉ", color="#3B82F6"))
    assert w.repo.items[cid].name == "CAFÉ" and w.repo.items[cid].color == "#3B82F6"


async def test_las_predeterminadas_se_pueden_renombrar() -> None:
    w = World()
    await w.defaults.execute(w.user)
    ocio = w.by_name("Ocio")
    await w.upsert.execute(w.user, w.input(ocio.id, "Diversión"))
    renamed = w.repo.items[ocio.id]
    assert renamed.name == "Diversión" and renamed.is_default  # sigue marcada como original


@pytest.mark.parametrize("name", ["", "   ", "x" * 31])
async def test_nombre_de_1_a_30_caracteres(name: str) -> None:
    with pytest.raises(InvalidCategoryNameError):
        await World().create(name)


async def test_nombre_de_30_caracteres_es_valido() -> None:
    await World().create("x" * 30)


async def test_nombre_cuya_normalizacion_excede_30_se_rechaza() -> None:
    with pytest.raises(InvalidCategoryNameError):
        await World().create("ﬃ" * 20)  # cada ligadura se expande a 3 letras


async def test_tipo_icono_y_color_deben_ser_del_catalogo() -> None:
    w = World()
    cid = uuid.uuid4()
    with pytest.raises(InvalidCategoryTypeError):
        await w.upsert.execute(w.user, w.input(cid, "A", "transfer"))
    with pytest.raises(InvalidIconError):
        await w.upsert.execute(w.user, w.input(cid, "A", icon="<script>"))
    with pytest.raises(InvalidColorError):
        await w.upsert.execute(w.user, w.input(cid, "A", color="#123456"))
    assert not w.repo.items


async def test_el_color_se_guarda_en_mayusculas() -> None:
    w = World()
    cid = uuid.uuid4()
    await w.upsert.execute(w.user, w.input(cid, "A", color="#f97316"))
    assert w.repo.items[cid].color == "#F97316"


async def test_cambiar_el_tipo_se_permite_si_la_categoria_no_se_usa() -> None:
    w = World()
    cid = await w.create("Nueva")
    await w.upsert.execute(w.user, w.input(cid, "Nueva", "income"))
    assert w.repo.items[cid].type == "income"


@pytest.mark.parametrize("module", ["tx", "rules", "budgets"])
async def test_no_se_cambia_el_tipo_si_algun_modulo_la_usa(module: str) -> None:
    w = World()
    cid = await w.create("Usada")
    getattr(w, module).used.add(cid)
    with pytest.raises(CategoryTypeLockedError):
        await w.upsert.execute(w.user, w.input(cid, "Usada", "income"))
    assert w.repo.items[cid].type == "expense"


async def test_una_categoria_usada_si_se_puede_renombrar_sin_cambiar_el_tipo() -> None:
    w = World()
    cid = await w.create("Usada")
    w.tx.used.add(cid)
    await w.upsert.execute(w.user, w.input(cid, "Renombrada"))


async def test_categoria_ajena_se_trata_como_inexistente() -> None:
    w = World()
    other = uuid.uuid4()
    cid = await w.create("De otro", user=other)
    with pytest.raises(CategoryNotFoundError):
        await w.upsert.execute(w.user, w.input(cid, "Robada"))
    assert w.repo.items[cid].name == "De otro" and w.repo.items[cid].user_id == other


async def test_no_se_edita_una_categoria_eliminada() -> None:
    w = World()
    cid = await w.create("Vieja")
    await w.create("Otra")
    await w.delete.execute(w.user, cid)
    with pytest.raises(CategoryNotFoundError):
        await w.upsert.execute(w.user, w.input(cid, "Revivida"))
