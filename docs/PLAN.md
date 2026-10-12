# Plan de ejecución del backend

Estado: **aprobado** (2026-10-12).
Fuente de verdad: [BLUEPRINT.md](../BLUEPRINT.md). Las decisiones y sus razones están en [DECISIONS.md](DECISIONS.md). Cada fase actualiza el registro de progreso al final de este archivo.

## Alcance

Todo lo que el Blueprint asigna al backend (secciones 5, 6.2, 6.3, 6.4): módulos `auth`, `categories`, `transactions`, `recurring`, `budgets` y `sync`, más infraestructura (Docker, migraciones, CI). Las HU11, HU12, HU13 y HU15 viven en el navegador y **no** llevan endpoints.

Fuera de alcance: frontend, verificación de correo, 2FA, cambio de moneda, notificaciones push.

## Orden y razón

Se implementa de adentro hacia afuera dentro de cada módulo (dominio → aplicación → infraestructura → API) y en este orden entre módulos, porque cada uno depende del anterior:

| Fase | Contenido | HU | Depende de |
|---|---|---|---|
| 0 | Andamiaje: `backend/`, `uv`, Ruff, mypy, pytest, `docker-compose` (Postgres 16 + Redis 7), config, `Clock`, errores de dominio, app FastAPI vacía, `/health` | – | – |
| 1 | Base de datos: modelos SQLAlchemy, migración inicial Alembic (4 tablas sincronizables + 3 de acceso, secuencia `sync_version_seq`, índices y `CHECK`) | – | 0 |
| 2 | `auth`: registro, login, refresh con rotación y familias, logout (`?all=true`), `/me`, límite de intentos (Redis), recuperar/restablecer contraseña, cola de correo (ARQ) | HU01–03 | 1 |
| 3 | `categories`: CRUD, categorías por defecto al registrar (se conecta a HU01), `name_key`, reasignación al eliminar, mínimo una por tipo | HU08 | 2 |
| 4 | `transactions`: validaciones (monto, fecha vía `Clock`, tipo = tipo de categoría, 5 etiquetas, normalización), tipo inmutable, borrado lógico | HU04–07, HU10 | 3 |
| 5 | `recurring`: validación y almacenamiento de reglas (`CHECK` fin por fecha o por conteo, `generate_from`) | HU09 | 3 |
| 6 | `budgets`: un presupuesto por categoría de gasto y mes, `effective_from` día 1 | HU14 | 3 |
| 7 | `sync`: `push` idempotente (orden categorías → reglas → movimientos → presupuestos, rechazos por cambio) y `pull` paginado por `version` | todas | 3–6 |
| 8 | Cierre: CI en GitHub Actions, cobertura de `domain`/`application`, revisión de seguridad, OpenAPI exportado para `ng-openapi-gen` | – | 7 |

## Estructura objetivo

```
backend/
  pyproject.toml
  alembic.ini · migrations/
  app/
    main.py · config.py
    shared/            Clock, errores base, UnitOfWork, seguridad común
    modules/<módulo>/{api,application,domain,infrastructure}
  tests/{unit,integration}/
docker-compose.yml
docs/{PLAN.md,DECISIONS.md}
```

## Cómo se prueba

- **Unitarias** de `domain` y `application` con puertos falsos (sin red ni BD).
- **Integración** contra PostgreSQL real (no SQLite: se usan `TEXT[]`, secuencias, índices parciales y `CHECK`). Redis y correo se sustituyen por adaptadores en memoria.
- Cada criterio de aceptación y regla de negocio del Blueprint tiene al menos una prueba nombrada tras el escenario.
- Puerta de salida de cada fase: `ruff check`, `ruff format --check`, `mypy app`, `pytest` en verde.

## Preguntas abiertas (necesito tu respuesta antes de la fase indicada)

1. **Ubicación del código** (fase 0). El Blueprint pide `backend/` dentro de un monorepo con `frontend/`, pero este repo se llama BackFinanzas. Propuesta: `backend/` tal como dice el Blueprint (ver D-01).
2. **Proveedor de correo** (fase 2). Propuesta: puerto `EmailSender` con adaptador que escribe en el log para desarrollo y adaptador SMTP/Resend para producción, que quedaría sin configurar hasta que elijas (ver D-09).
3. **README.md** está vacío, pero el Blueprint lo cita para el glosario y las reglas de estilo. Propuesta: aplicar las reglas de `AGENTS.md` (sección 7.1 del Blueprint) y no escribir ese README salvo que lo pidas.
4. **Archivos `AGENTS.md` y `CLAUDE.md`** no existen aunque el Blueprint dice copiarlos. Propuesta: crearlos tal cual en la fase 0.

## Registro de progreso

| Fase | Estado | Notas |
|---|---|---|
| 0 | ✅ hecha (2026-10-12) | Ruff, mypy estricto y 4 pruebas en verde; Postgres y Redis arriba y sanos |
| 1 | ✅ hecha (2026-10-12) | Migración `0001`, 13 pruebas de integración del esquema contra Postgres real, `alembic check` sin diferencias; 17 pruebas en total |
| 2 | ✅ hecha (2026-10-12) | HU01–HU03 completas: 78 pruebas en total; `application` y `domain` de `auth` al 100 %; probado de extremo a extremo con Redis y ARQ reales. Pendiente de la fase 3: sustituir `NullDefaultCategoriesSeeder` por el real (HU01 pide las 12 categorías) |
| 3 | ✅ hecha (2026-10-12) | HU08 completa y HU01 cerrada (el registro crea las 12 categorías). 129 pruebas; `domain`/`application` de `categories` al 100 %. Sin router: las categorías viajan por `sync` (fase 7), que llamará a `UpsertCategory` y `DeleteCategory` |
| 4 | ✅ hecha (2026-10-12) | HU04–HU07 y HU10: 189 pruebas en total; `domain`/`application` de `transactions` al 100 %. Sin router (van por `sync`, fase 7) |
| 5 | ✅ hecha (2026-10-12) | HU09 (lado servidor): 234 pruebas en total; `domain`/`application` de `recurring` al 100 %. Sin router (van por `sync`). La generación de ocurrencias y el cálculo de fechas son del navegador |
| 6 | ✅ hecha (2026-10-12) | HU14 (lado servidor): `UpsertBudget` y `DeleteBudget`, sin router (van por `sync`). Cálculo de gastado, barras y alertas son del navegador |
| 7 | ✅ hecha (2026-10-12) | `POST /sync/push` y `GET /sync/pull`: 267 pruebas en total; `application` de `sync` al 100 %. Cierra HU01–HU10 y HU14 de extremo a extremo por HTTP |
| 8 | ✅ hecha (2026-10-12) | CI en `.github/workflows/backend.yml`, cobertura total 98 % (`domain`/`application` al 100 %), CORS, guarda del correo de desarrollo, `backend/openapi.json` y revisión de seguridad (D-47). 268 pruebas |
