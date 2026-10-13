# AGENTS.md

Instrucciones para cualquier agente de IA que trabaje en este repositorio.

## Contexto

Estás desarrollando una app web de gastos personales que **funciona sin conexión**. El usuario registra gastos e ingresos, los organiza por categorías y etiquetas, programa pagos recurrentes, consulta su historial y resumen del mes, y controla presupuestos con gráficos.

- **Frontend:** PWA en Angular. Los datos viven en el navegador con Dexie (IndexedDB) y se sincronizan con el servidor.
- **Backend:** FastAPI con PostgreSQL, organizado como monolito modular con arquitectura hexagonal.

Las fuentes de verdad son:
1. `BLUEPRINT.md`: qué construir (historias, reglas, criterios de aceptación, modelo de datos, API).
2. `README.md`: cómo construirlo (código limpio, capas, seguridad, rendimiento, pruebas, Git).

Si algo no está en estos documentos o se contradicen, **pregunta antes de asumir**. Si este archivo y `BLUEPRINT.md` no coinciden, manda `BLUEPRINT.md`.

## Estructura del repositorio

```
BLUEPRINT.md         Qué construir
README.md            Cómo construirlo
AGENTS.md            Este archivo
CLAUDE.md            Importa este archivo para Claude Code
docker-compose.yml   PostgreSQL y Redis para desarrollo
backend/             FastAPI. Cada módulo en app/modules/<módulo>/{api,application,domain,infrastructure}
frontend/            Angular. Cada funcionalidad en src/app/features/<funcionalidad>/{pages,components,data,domain}
```

## Comandos

- Levantar PostgreSQL y Redis: `docker compose up -d`
- Backend (dentro de `backend/`): `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest`
- Frontend (dentro de `frontend/`): `npm run lint && npm run test:ci && npm run build`
- Si cambias un endpoint, regenera el cliente de la API con `ng-openapi-gen` antes de usarlo en el frontend.

## Cómo trabajar una historia

1. **Lee la historia completa** en `BLUEPRINT.md`: reglas de negocio, criterios de aceptación y casos límite.
2. **Revisa el código existente** del módulo antes de escribir. Reutiliza lo que ya existe y sigue el mismo estilo.
3. **Propón un plan corto** (archivos a crear o modificar, por capa) antes de cambios grandes.
4. **Escribe las pruebas junto con el código.** Cada criterio de aceptación y cada regla de negocio debe quedar cubierto por al menos una prueba.
5. **Implementa de adentro hacia afuera:** dominio → aplicación → infraestructura → API (backend); dominio → repositorio → página y componentes (frontend).
6. **Ejecuta los comandos de arriba y déjalos en verde.**
7. **Reporta** al terminar (ver formato abajo).

## Reglas que no se rompen

- **Capas:**
  - El dominio no importa FastAPI, Pydantic, SQLAlchemy, Angular ni Dexie.
  - Los routers y los componentes no contienen lógica de negocio.
  - Los componentes nunca usan `HttpClient` ni Dexie directamente: todo pasa por un repositorio.
- **Entre módulos:** un módulo solo usa lo que otro expone en su capa `application`. Nunca consulta tablas ajenas.
- **Modelo de datos** (detalle en la sección 6.3 de `BLUEPRINT.md`):
  - **Dinero:** siempre entero en centavos (`amount_minor`). Nunca `float` ni `number` con decimales para montos guardados.
  - **IDs:** UUID generados en el cliente. Las ocurrencias recurrentes usan `uuidv5(fecha ISO, ruleId)`.
  - **Versión:** `version` solo la asigna el servidor, con la secuencia global. El cliente nunca la inventa.
  - **Nombres de categoría:** la unicidad se revisa con `name_key` (minúsculas y sin tildes), calculado en el dominio.
- **Borrado:** siempre lógico (`deleted_at`). Nunca borres físicamente datos sincronizables. No purgues las marcas de borrado del navegador: evitan que se regeneren recurrencias.
- **Seguridad:**
  - Toda consulta filtra por el `user_id` del token. Nunca aceptes `user_id` del body o de la URL.
  - Esquemas de entrada con `extra="forbid"` y límites.
  - Sin secretos en el código ni en `environment.ts`.
  - Sin datos sensibles en logs.
  - No uses `bypassSecurityTrust*` ni `innerHTML` con datos del usuario.
- **Sin conexión:**
  - Toda escritura del usuario se guarda en Dexie y en el `outbox` **en la misma transacción**.
  - La UI nunca espera al servidor para guardar.
- **Tiempo:** inyecta un `Clock`. Nunca llames a `datetime.now()`, `date.today()` ni `new Date()` dentro del dominio.
- **Esquemas:**
  - Cambios de base de datos solo con una **nueva** migración de Alembic. Nunca edites una migración ya aplicada.
  - En Dexie, solo con una **nueva** `version(n)`.
- **Pruebas:**
  - No desactives, borres ni debilites una prueba para que pase.
  - Si una prueba falla, arregla el código o explica por qué la prueba está mal.
- **Dependencias:** no agregues librerías nuevas sin justificarlo y sin preguntar.
- **Alcance:** implementa solo lo que pide la historia. Lo marcado como "Fuera de alcance" no se construye.

## Convenciones

- **Código** (identificadores, tablas, endpoints) **en inglés**, según el glosario del README. **Textos de la interfaz, comentarios y commits en español.**
- **Angular:**
  - Componentes standalone, `OnPush`, signals, `inject()`, `input()` / `output()`.
  - `@if` / `@for` con `track`.
  - Formularios reactivos tipados.
- **Python:**
  - Type hints en todo.
  - Dataclasses para el dominio y `Protocol` para los puertos.
  - Un caso de uso por clase, con método `execute`.
- **Errores de dominio** con clase propia; la API los traduce a HTTP 422 con `code` y `message`.
- **Commits** con Conventional Commits en español, indicando la historia: `feat(transactions): registrar gasto sin conexión (HU04)`.

## Cuándo detenerte y preguntar

- Un criterio de aceptación es ambiguo o dos documentos se contradicen.
- La solución requiere cambiar el modelo de datos, el protocolo de sincronización o una regla de `BLUEPRINT.md`.
- Necesitas una dependencia nueva o un servicio externo.
- Una prueba existente falla por algo que no tocaste.

## Formato del reporte al terminar

```
Historia: HU__
Cambios:
- backend/app/modules/…: qué se hizo
- frontend/src/app/features/…: qué se hizo
Pruebas: N nuevas; cobertura de domain/application: __ %
Criterios de aceptación → prueba que lo verifica:
- "Registrar sin conexión" → transaction.repository.spec.ts › guarda el movimiento y lo encola
Comandos ejecutados y resultado: lint ✅ tipos ✅ pruebas ✅ build ✅
Pendientes o dudas:
```
