# Documentación técnica de BackFinanzas

## 1. Propósito y estado del proyecto

BackFinanzas es una aplicación de finanzas personales diseñada para trabajar sin conexión. El
servidor conserva la copia oficial de los datos y los dispositivos mantienen una copia local que
se sincroniza cuando hay conectividad.

En el estado actual del repositorio se encuentra implementado el backend, que expone:

- autenticación y gestión de sesiones;
- recuperación de contraseña;
- categorías, movimientos, reglas recurrentes y presupuestos mediante sincronización;
- sincronización incremental `push`/`pull`;
- persistencia en PostgreSQL;
- límites de intentos mediante Redis;
- migraciones Alembic;
- pruebas unitarias, de integración, seguridad y aceptación;
- validación automática en GitHub Actions.

El frontend Angular, la PWA y la base local Dexie están definidos en el Blueprint como parte del
producto objetivo, pero no forman parte del código presente en este repositorio. Las pantallas
descritas en el manual de usuario deben considerarse el contrato funcional del frontend.

## 2. Arquitectura

El backend es un monolito modular con arquitectura hexagonal. Cada módulo está organizado en:

```text
api -> application -> domain <- infrastructure
```

- `api`: routers HTTP y esquemas de entrada/salida.
- `application`: casos de uso y puertos que necesita el módulo.
- `domain`: entidades, reglas y errores de negocio independientes de FastAPI y SQLAlchemy.
- `infrastructure`: repositorios, modelos SQLAlchemy y adaptadores externos.

### 2.1. Módulos

| Módulo | Responsabilidad |
|---|---|
| `auth` | Usuarios, contraseñas, JWT, refresh tokens, logout y recuperación |
| `categories` | Categorías predeterminadas, categorías personalizadas y reasignación |
| `transactions` | Gastos, ingresos, etiquetas, notas y borrado lógico |
| `recurring` | Reglas de movimientos recurrentes |
| `budgets` | Presupuestos mensuales por categoría |
| `sync` | Aplicación y consulta incremental de cambios |
| `shared` | Reloj, errores, unidad de trabajo, base de datos y utilidades comunes |

La composición de dependencias se centraliza en `backend/app/composition.py`. Los módulos no
consultan directamente las tablas de otros módulos; se comunican mediante puertos de aplicación.

## 3. Tecnologías

| Área | Tecnología |
|---|---|
| Runtime | Python 3.12 o superior |
| API | FastAPI, Pydantic v2, Uvicorn |
| Persistencia | PostgreSQL 16, SQLAlchemy 2 async, asyncpg |
| Migraciones | Alembic |
| Caché y rate limiting | Redis 7 |
| Cola de correo | ARQ, mediante el puerto `EmailSender` |
| Contraseñas | Argon2id mediante `pwdlib` |
| Tokens | PyJWT y refresh token opaco |
| Calidad | Ruff, mypy estricto, pytest, pytest-cov |
| CI | GitHub Actions |

## 4. Ejecución local

### 4.1. Requisitos

- Python 3.12+.
- `uv`.
- Docker Desktop con el daemon activo.
- Git.

### 4.2. Servicios de infraestructura

Desde la raíz:

```powershell
docker compose up -d
docker compose ps
```

El archivo `docker-compose.yml` inicia:

| Servicio | Imagen | Puerto local |
|---|---|---:|
| PostgreSQL | `postgres:16` | `5433` |
| Redis | `redis:7` | `6380` |

### 4.3. Configuración del backend

Desde `backend/`, copiar `.env.example` a `.env` y completar al menos:

```dotenv
DATABASE_URL=postgresql+asyncpg://finanzas:finanzas@localhost:5433/finanzas
REDIS_URL=redis://localhost:6380/0
JWT_SECRET=una-clave-de-al-menos-32-caracteres
FRONTEND_URL=http://localhost:4200
COOKIE_SECURE=false
```

`COOKIE_SECURE=false` solo debe usarse en desarrollo local con HTTP. En producción debe ser
`true` y la API debe publicarse detrás de HTTPS.

### 4.4. Instalación, migraciones y arranque

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Comprobaciones:

```powershell
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

La documentación interactiva de FastAPI queda disponible en `/docs` y el esquema OpenAPI en
`backend/openapi.json`.

## 5. Configuración

La configuración se carga desde variables de entorno y `.env` mediante
`backend/app/config.py`.

| Variable | Obligatoria | Valor por defecto | Uso |
|---|---:|---|---|
| `DATABASE_URL` | No | PostgreSQL local | Conexión async a PostgreSQL |
| `REDIS_URL` | No | Redis local | Rate limiting y cola |
| `JWT_SECRET` | Sí | Ninguno | Firma de access tokens |
| `ACCESS_TOKEN_MINUTES` | No | `15` | Vida del JWT |
| `REFRESH_TOKEN_DAYS` | No | `30` | Vida inicial del refresh |
| `COOKIE_SECURE` | No | `true` | Atributo seguro de la cookie |
| `FRONTEND_URL` | No | `http://localhost:4200` | Origen permitido por CORS |

No se deben almacenar secretos en el repositorio ni en el frontend.

## 6. Contrato HTTP

Base local: `http://localhost:8000`.

| Método | Ruta | Autenticación | Descripción |
|---|---|---|---|
| `POST` | `/auth/register` | No | Registra una cuenta y devuelve sesión |
| `POST` | `/auth/login` | No | Inicia sesión |
| `POST` | `/auth/refresh` | Cookie | Rota el refresh token |
| `POST` | `/auth/logout` | Cookie | Cierra la sesión actual |
| `POST` | `/auth/logout?all=true` | Cookie | Cierra todas las sesiones |
| `POST` | `/auth/password/forgot` | No | Solicita recuperación |
| `POST` | `/auth/password/reset` | No | Cambia la contraseña usando el token |
| `GET` | `/me` | Bearer | Consulta la cuenta autenticada |
| `POST` | `/sync/push` | Bearer | Envía cambios locales |
| `GET` | `/sync/pull` | Bearer | Descarga cambios desde una versión |
| `GET` | `/health` | No | Verifica disponibilidad de la API |

Los endpoints protegidos reciben:

```http
Authorization: Bearer <access_token>
```

El refresh token no se devuelve en JSON. Se almacena en una cookie `HttpOnly`, `SameSite=Strict`,
con ruta `/auth`.

### 6.1. Registro y login

Ejemplo de registro:

```json
{
  "email": "ana@correo.com",
  "password": "ClaveSegura1",
  "password_confirmation": "ClaveSegura1",
  "currency": "COP"
}
```

La respuesta contiene el access token y los datos públicos del usuario. La contraseña, su hash y
el refresh token nunca se incluyen en la respuesta.

### 6.2. Sincronización

`POST /sync/push` recibe cambios locales:

```json
{
  "changes": [
    {
      "entity": "transaction",
      "op": "upsert",
      "id": "00000000-0000-0000-0000-000000000001",
      "data": {
        "type": "expense",
        "amount_minor": 250000,
        "category_id": "00000000-0000-0000-0000-000000000002",
        "occurred_on": "2026-10-12"
      }
    }
  ]
}
```

La respuesta separa cambios aplicados y rechazados:

```json
{
  "applied": ["00000000-0000-0000-0000-000000000001"],
  "rejected": [],
  "version": 18423
}
```

`GET /sync/pull?since=18400&limit=500` devuelve cambios posteriores al cursor. El cliente debe
repetir la petición mientras `has_more` sea `true` y continuar desde `next_since`.

Reglas importantes:

- el servidor asigna `version`;
- los cambios se aplican en orden de categorías, reglas, movimientos y presupuestos;
- reenviar el mismo UUID es idempotente;
- un cambio inválido no invalida los cambios válidos del mismo lote;
- cada usuario solo puede leer y modificar sus propios datos;
- los borrados son lógicos y conservan la marca `deleted_at`.

## 7. Modelo de datos y reglas

Las tablas sincronizables son `categories`, `transactions`, `recurring_rules` y `budgets`.

- Los importes se almacenan en centavos enteros en `amount_minor`.
- Los identificadores son UUID.
- Las categorías se comparan mediante `name_key`, normalizado a minúsculas y sin tildes.
- Un movimiento no puede cambiar de tipo después de creado.
- Una fecha de movimiento futura se rechaza.
- Una categoría con entidades asociadas requiere una categoría de reasignación al eliminarse.
- Solo puede existir un presupuesto activo por categoría y mes.
- Las consultas se filtran siempre por el usuario autenticado.

Las migraciones existentes no deben editarse. Todo cambio de esquema requiere una nueva migración:

```powershell
cd backend
uv run alembic revision -m "describe el cambio"
uv run alembic upgrade head
```

## 8. Seguridad

- Contraseñas con Argon2id.
- JWT de corta duración para acceso.
- Refresh tokens aleatorios, almacenados como hash y rotados por familia.
- Revocación de toda la familia si se reutiliza un refresh token revocado.
- Rate limiting de login y recuperación mediante Redis.
- Respuestas opacas para recuperación de cuentas inexistentes.
- Esquemas de entrada estrictos (`extra="forbid"`).
- CORS limitado al origen del frontend configurado.
- Sin `user_id` aceptado desde el body o la URL.
- Sin secretos ni datos sensibles en logs de producción.

## 9. Pruebas y calidad

Desde `backend/`:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest --cov=app --cov-report=term-missing
```

La suite está organizada en:

```text
tests/unit/
tests/integration/
tests/security/
tests/acceptance/
```

Las pruebas de integración requieren PostgreSQL y Redis disponibles. La cobertura y los resultados
deben tomarse de la ejecución real; `docs/TESTING.md` describe la estrategia y los casos cubiertos.

## 10. CI/CD: sección reservada para creación y revisión

Actualmente existe un workflow de validación en
`.github/workflows/backend.yml`. Ejecuta Ruff, mypy, pytest con cobertura y verifica que
`backend/openapi.json` esté actualizado. No se documenta aquí un despliegue automático porque todavía
no hay una plataforma, un registro de imágenes, ambientes ni secretos de despliegue definidos.

### 10.1. Pendientes de definición

- plataforma de destino;
- ambientes (`staging`, `production`);
- estrategia de migraciones en despliegue;
- registro de imágenes, si se usa contenedorización;
- gestión de secretos;
- aprobaciones y protección de ramas;
- estrategia de rollback;
- observabilidad y alertas;
- revisión del pipeline existente y sus permisos.

### 10.2. Espacio para la futura revisión

> **Estado:** pendiente de creación/revisión del pipeline de integración y despliegue.
>
> **Responsable:** ____________________  
> **Fecha de revisión:** ____________________  
> **Plataforma objetivo:** ____________________  
> **Resultado:** ____________________  
> **Hallazgos y acciones:**  
> - __________________________________________  
> - __________________________________________  

## 11. Referencias

- [Blueprint del producto](../BLUEPRINT.md)
- [Plan de ejecución](PLAN.md)
- [Decisiones técnicas](DECISIONS.md)
- [Estrategia de pruebas](TESTING.md)
- [Workflow de backend](../.github/workflows/backend.yml)
