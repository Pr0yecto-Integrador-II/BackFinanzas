# Documentación del Plan y Suite de Pruebas

Este documento detalla la estrategia, estructura, cobertura y guía de ejecución de la suite de pruebas automatizadas del backend de la aplicación.

---

## 1. Resumen General

La suite de pruebas cuenta con **319 pruebas automatizadas** divididas en 4 niveles de prueba siguiendo la pirámide de testing y la arquitectura hexagonal del sistema:

| Tipo de Prueba | Enfoque | Tecnologías | Cantidad | Ubicación |
|---|---|---|---|---|
| **Unitarias** | Reglas de negocio puras, lógica de dominio y casos de uso con fakes en memoria. | `pytest`, `pytest-asyncio` | 212 | `tests/unit/` |
| **Integración** | Persistencia real en PostgreSQL, migraciones de Alembic, concurrencia y bloqueos. | `pytest`, `SQLAlchemy`, `asyncpg`, `Alembic` | 56 | `tests/integration/` |
| **Seguridad** | Autenticación, JWT, aislamiento multi-usuario, rate limiting, sanitización y CORS. | `pytest`, `httpx` (ASGI) | 23 | `tests/security/` |
| **Aceptación (BDD)** | Criterios de aceptación de negocio e Historias de Usuario (HU) en Gherkin. | `pytest-bdd`, `httpx` (ASGI) | 28 | `tests/acceptance/` |
| **TOTAL** | | | **319** | `tests/` |

---

## 2. Niveles de Pruebas

```
                   ▲
                  / \
                 /   \     Aceptación (BDD) - 28 escenarios
                /-----\    Seguridad - 23 pruebas
               /       \   Integración - 56 pruebas
              /---------\
             /           \  Unitarias - 212 pruebas
            /-------------\
```

### 2.1. Pruebas Unitarias (`tests/unit/`)
Prueban la lógica aislada sin dependencias externas (sin base de datos, sin red, sin I/O).
* **Módulos cubiertos:**
  * `auth`: Registro, validación de contraseñas, hashing, rotación de tokens, restablecimiento y mailer.
  * `categories`: Creación de 12 categorías predeterminadas, normalización de `name_key` (sin tildes, minúsculas), reasignación obligatoria al eliminar categorías con movimientos.
  * `transactions`: Inmutabilidad del tipo (`income`/`expense`), validación de fechas (no futuras), deduplicación y sanitización de etiquetas (`#tag`), montos en centavos enteros (`amount_minor`).
  * `recurring`: Generación de reglas recurrentes, validación de frecuencias (`monthly`, `weekly`).
  * `budgets`: Control de topes presupuestales por categoría y vigencias.
  * `sync`: Construcción de lotes de sincronización offline, lógica de `push` y `pull`.

### 2.2. Pruebas de Integración (`tests/integration/`)
Prueban la interacción directa con los servicios reales definidos en el entorno Docker.
* **Infraestructura:**
  * Base de datos PostgreSQL real (`finanzas_test` en el puerto 5433).
  * Migraciones completas de Alembic aplicadas automáticamente al iniciar la sesión (`migrated_database`).
  * Redis para límites de peticiones (`FakeLimiter` y `RedisLimiter`).
  * Transacciones de prueba con rollback automático por cada test (`conn`, `session`).

### 2.3. Pruebas de Seguridad (`tests/security/`)
Verifican el cumplimiento de las políticas de seguridad del sistema:
* **Autenticación (SEC-AUTH):** Rechazo de accesos no autorizados (HTTP 401) en endpoints protegidos (`/sync/pull`, `/sync/push`, `/auth/me`, `/auth/refresh`).
* **Protección contra ataques de fuerza bruta:** Bloqueo automático (HTTP 429) tras 5 intentos fallidos consecutivos de login.
* **Prevención de enumeración de usuarios:** Respuestas y tiempos idénticos tanto para correos existentes como inexistentes al autenticar o solicitar recuperación de clave.
* **Aislamiento Multi-usuario (SEC-AUTHZ):**
  * Ningún usuario puede consultar datos de otro usuario.
  * Un usuario no puede registrar movimientos usando categorías que pertenecen a otro usuario.
  * Un usuario no puede sobrescribir el UUID de una entidad perteneciente a otro usuario.
* **Protección de Datos Sensibles (SEC-SECRETS):**
  * Los hashes de contraseñas nunca se exponen en las respuestas de la API.
  * El `refresh_token` viaja estrictamente en una cookie `HttpOnly` y jamás en el cuerpo (`body`) JSON.
* **Control de Entrada y CORS (SEC-INPUT / SEC-CORS):**
  * Esquemas Pydantic con `extra="forbid"` (se rechaza cualquier campo no esperado como `user_id` en el body).
  * Montos numéricos validados estrictamente como enteros (`amount_minor`), rechazando flotantes o decimales.
  * Orígenes no autorizados no reciben encabezados CORS permisivos.

### 2.4. Pruebas de Aceptación BDD (`tests/acceptance/`)
Escritas en lenguaje natural estructurado (Gherkin en español) para validar el comportamiento del sistema desde la perspectiva del usuario final:

#### Archivos `.feature` y escenarios implementados:
1. **`features/auth/registro.feature` (HU01 - 4 escenarios):**
   * Registro exitoso devuelve sesión y crea categorías por defecto.
   * Rechazo de registro con correo ya existente (409 Conflict).
   * Validación de contraseña (mínimo 1 letra y 1 número).
   * Rechazo de campos extra en el formulario de registro.
2. **`features/auth/login.feature` (HU02 - 4 escenarios):**
   * Login exitoso devuelve token de acceso y cookie `HttpOnly`.
   * Credenciales incorrectas devuelven mensaje genérico.
   * Correo inexistente devuelve el mismo mensaje que contraseña incorrecta.
   * Bloqueo de cuenta tras 5 intentos fallidos (Rate Limit 429).
3. **`features/auth/recuperacion.feature` (HU03 - 4 escenarios):**
   * Envío de correo al solicitar recuperación con email existente.
   * Respuesta opaca idéntica si el correo no existe.
   * Restablecimiento exitoso revoca todas las sesiones y tokens previos.
   * Un solo uso permitido por cada token de recuperación.
4. **`features/sync/movimientos.feature` (HU04 a HU07, HU10 - 7 escenarios):**
   * Registro y recuperación de gastos con centavos enteros en el sync.
   * El tipo de un movimiento no se puede cambiar (`TransactionTypeLockedError`).
   * Rechazo de gastos con fechas futuras (`FutureDateError`).
   * Normalización y deduplicación de etiquetas (tags en minúsculas y sin `#`).
   * Borrado lógico (`deleted_at`) e idempotencia.
   * Tolerancia a fallos: un cambio inválido en un lote no cancela los cambios válidos.
   * Reenvío del mismo cambio no duplica el registro (idempotencia por UUID).
5. **`features/sync/categorias.feature` (HU08 - 4 escenarios):**
   * Creación automática de 12 categorías por defecto (9 gastos, 3 ingresos).
   * Eliminación de categoría con movimientos exige categoría de reasignación.
   * Reasignación automática de movimientos a la nueva categoría al eliminar.
   * Aislamiento de categorías entre usuarios distintos.
6. **`features/sync/sincronizacion.feature` (Protocolo Sync - 5 escenarios):**
   * Pull incremental usando cursor global `since`.
   * Paginación de resultados con `limit`, `has_more` y `next_since`.
   * Sincronización de reglas recurrentes (`recurring_rule`) y presupuestos (`budget`).
   * Rechazo completo de lotes con más de 500 cambios (límite de seguridad).
   * Aislamiento multi-inquilino estricto en operaciones de push.

---

## 3. Requisitos Previos

Antes de ejecutar las pruebas de integración, seguridad o aceptación, los servicios de base de datos y caché deben estar activos:

```bash
docker compose up -d
```

Verificar que los contenedores estén saludables:
```bash
docker compose ps
```
* **PostgreSQL:** puerto `5433` (mapeado a `5432` en el contenedor).
* **Redis:** puerto `6380` (mapeado a `6379` en el contenedor).

---

## 4. Guía de Ejecución

Todos los comandos deben ejecutarse dentro de la carpeta `backend/`:

```bash
cd backend
```

### 4.1. Toda la Suite
Ejecuta los 319 tests:
```bash
uv run pytest
```
Con detalle paso a paso:
```bash
uv run pytest -v
```

### 4.2. Por Nivel de Prueba
* **Solo Aceptación (BDD):**
  ```bash
  uv run pytest tests/acceptance/ -v
  ```
* **Solo Seguridad:**
  ```bash
  uv run pytest tests/security/ -v
  ```
* **Solo Unitarias:**
  ```bash
  uv run pytest tests/unit/ -v
  ```
* **Solo Integración:**
  ```bash
  uv run pytest tests/integration/ -v
  ```

### 4.3. Por Archivo o Escenario Específico
* **Un archivo de pruebas:**
  ```bash
  uv run pytest tests/security/test_security.py -v
  ```
* **Una prueba en particular:**
  ```bash
  uv run pytest tests/security/test_security.py::test_bloqueo_tambien_con_clave_correcta_tras_5_fallos -v
  ```
* **Filtrar por texto/palabra clave (`-k`):**
  ```bash
  uv run pytest -k "bloqueo" -v
  uv run pytest -k "recuperacion" -v
  ```

### 4.4. Cobertura de Código (Coverage)
Para generar el informe de cobertura sobre el paquete `app`:
```bash
uv run pytest --cov=app --cov-report=term-missing
```

---

## 5. Verificación de Calidad y Estilo

El proyecto utiliza reglas estrictas de tipado y estilo que deben mantenerse en verde:

```bash
# 1. Revisión de linter (Ruff)
uv run ruff check .

# 2. Verificación de formato de código
uv run ruff format --check .

# 3. Comprobación estricta de tipos estáticos
uv run mypy app
```
