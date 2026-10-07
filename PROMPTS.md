# 3 prompts para construir el Blueprint de la App de Gastos Personales


## 1. Buenas prácticas aplicadas (investigadas en la web)

Fuentes: [Prompting best practices (Anthropic)](https://platform.claude.com/en/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Use XML tags (Anthropic)](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags), [Best practices for prompt engineering (Claude)](https://www.claude.com/blog/best-practices-for-prompt-engineering), [Prompt Engineering Best Practices 2026](https://thomas-wiegold.com/blog/prompt-engineering-best-practices-2026/), [Prompt Engineering Best Practices (2026): Checklist](https://promptbuilder.cc/blog/prompt-engineering-best-practices-2026).

| Buena práctica | Qué dicen las fuentes | Cómo se aplica aquí |
|---|---|---|
| **Etiquetas XML** | Separan instrucciones, contexto, ejemplos y entradas; reducen malinterpretaciones. Usar nombres consistentes y anidar si hay jerarquía. | Todos los prompts usan las mismas etiquetas: `<role>`, `<context>`, `<documents>`, `<task>`, `<instructions>`, `<constraints>`, `<examples>`, `<output_format>`, `<verification>`, `<stop_conditions>`. |
| **Asignar un rol** | Una sola frase en el rol ya cambia el enfoque y el tono. | Cada prompt abre con `<role>` distinto: analista de producto, arquitecto de software, ingeniero de plataforma para agentes. |
| **Ser claro y directo** | Explicar el objetivo y el *por qué* de cada restricción; decir qué hacer, no solo qué evitar. | Cada `<constraints>` lleva el motivo entre paréntesis. |
| **Criterios de éxito + contrato de salida** | En 2026 el prompting es escribir una especificación: qué es "terminado", formato, longitud y secciones obligatorias. | `<output_format>` fija la plantilla exacta; `<verification>` lista los criterios de terminado. |
| **Ejemplos (few-shot)** | 3–5 ejemplos relevantes y diversos dirigen el formato con mucha precisión. | `<examples>` incluye una historia modelo completa (Prompt 1), una tabla modelo (Prompt 2) y una regla modelo (Prompt 3). |
| **Encadenar prompts** | Dividir una tarea grande en pasos secuenciales pasando el resultado al siguiente da más coherencia. | 3 prompts en cadena, cada uno con su entregable. |
| **Documentos largos arriba, pregunta al final** | Poner el material extenso al inicio y la instrucción al final mejora la calidad. | `<documents>` va antes de `<task>`; la tarea cierra el prompt. |
| **Pensar antes de responder** | Pedir razonamiento previo en un bloque separado mejora tareas complejas. | `<thinking>` obligatorio antes de entregar, separado del resultado. |
| **Permiso para no saber** | Dar una salida ("pregunta si falta información") reduce inventos. | `<stop_conditions>` obliga a preguntar en vez de asumir. |
| **Autoverificación** | Pedir que el modelo revise su propia salida contra los criterios. | `<verification>` con casillas que el modelo marca al final. |
| **Contexto, no solo prompt** | Los fallos de agentes suelen ser de contexto: cargar solo lo necesario en cada paso. | Cada prompt recibe únicamente lo que necesita de los anteriores. |
| **Iterar y probar** | Los prompts se refinan con pruebas, no salen perfectos a la primera. | Sección 5 de este README: checklist de revisión por prompt. |

> Nota: las fuentes indican que no existen nombres de etiqueta "canónicos" entrenados en Claude; lo importante es que sean descriptivos y consistentes.

---

## 2. Prompt 1: Historias de usuario (el QUÉ)

~~~~xml
<role>
Eres un analista de producto senior especializado en aplicaciones de finanzas personales offline-first, con experiencia redactando historias de usuario, reglas de negocio y criterios de aceptación en Gherkin. Escribes en español claro, sin jerga innecesaria.
</role>

<context>
Vamos a documentar una app web de gastos personales que funciona sin conexión (PWA). Este documento será la fuente de verdad del producto: otros prompts y agentes de programación lo usarán para construir la app, así que cada regla debe ser precisa, comprobable y sin ambigüedades. Si una regla es vaga, el agente que programe tendrá que adivinar.
</context>

<documents>
<document index="1">
<source>Idea del producto</source>
<document_content>
App web de finanzas personales 
 App web para que joven profesional, independiente o estudiante sepa cuánto entra, cuánto sale y en qué se va, registrando en segundos y cuente con graficas.
</document_content>
</document>
</documents>

<task>
Redacta las secciones 1 a 4 del Blueprint:
1. Objetivo del documento.
2. Objetivo del producto (qué podrá hacer el usuario al completar las historias).
3. Conceptos base (tabla de glosario) y actores (Usuario, Sistema).
4. Las 15 historias de usuario, organizadas en 5 módulos, con un mapa inicial (módulo, HU, historia, entrega).
</task>

<instructions>
Estructura fija de los módulos y entregas:
- Módulo 1 Acceso: HU01 Registro (R1), HU02 Inicio y cierre de sesión (R1), HU03 Recuperar contraseña (R1).
- Módulo 2 Movimientos: HU04 Registrar gasto (R1), HU05 Registrar ingreso (R1), HU06 Editar (R1), HU07 Eliminar con deshacer de 5 s (R1).
- Módulo 3 Organización: HU08 Categorías personalizadas (R1), HU09 Movimientos recurrentes (R2), HU10 Notas y etiquetas (R2).
- Módulo 4 Consulta: HU11 Historial (R1), HU12 Búsqueda y filtros (R2), HU13 Resumen mensual (R2).
- Módulo 5 Control: HU14 Presupuesto por categoría (R3), HU15 Gráficos por categoría (R3).
- R1 incluye la sincronización sin conexión desde el inicio.

Cada historia debe contener, en este orden:
a) Encabezado `#### HUxx. Título`.
b) Frase "Como / quiero / para" en bloque de cita.
c) Contexto (1-2 frases: por qué existe), cuando aporte valor.
d) Reglas de negocio numeradas. Usa tablas para campos y validaciones. Indica siempre si requiere conexión o funciona sin ella.
e) Criterios de aceptación en Gherkin en español (Escenario / Dado / Cuando / Entonces / Y), con valores concretos (montos, fechas, textos exactos de los mensajes).
f) Casos límite (doble clic, primer uso, errores del servidor).
g) Fuera de alcance, explícito.

Decisiones de producto ya tomadas (no las cambies):
- Moneda única por cuenta, ISO 4217, por defecto COP, no se cambia en el MVP; los montos son enteros en centavos.
- Sesión de 30 días sin uso; bloqueo tras 5 intentos fallidos en 15 minutos; el cierre de sesión borra los datos locales y advierte si hay cambios sin sincronizar.
- El recuperar contraseña responde siempre con el mismo mensaje; enlace de 30 min y un solo uso; máximo 3 solicitudes por hora.
- El tipo de un movimiento y el de una categoría con movimientos no se pueden cambiar.
- Borrado siempre lógico.
- Conflictos de edición: gana el último cambio que llega al servidor.
- Recurrentes: diaria, semanal, quincenal (días 15 y último), mensual (si el día no existe, último del mes), anual (29 feb pasa a 28); modos automático y con confirmación; sin duplicados entre dispositivos; máximo 366 ocurrencias por regla.
- Presupuesto: se repite cada mes; alertas al 80 % y 100 % una sola vez por mes y categoría; nunca bloquea un gasto.
- HU11, HU12, HU13 y HU15 se resuelven en el navegador con datos locales.
</instructions>

<constraints>
- Cada regla debe poder verificarse con una prueba (así el agente que programe sabe cuándo terminó).
- Usa números y textos exactos en los escenarios Gherkin, nunca "un monto" o "un mensaje" (los textos exactos se vuelven pruebas de interfaz).
- No inventes funciones fuera de las 15 historias; lo no pedido va en "Fuera de alcance" (evita que se construya de más).
- Cada historia es independiente y legible por sí sola, porque un agente leerá una sola sección a la vez.
- Mínimo 3 escenarios Gherkin por historia, incluyendo un camino feliz y un error.
</constraints>

<examples>
<example>
#### HU07. Eliminar movimiento

> **Como** usuario,
> **quiero** eliminar un movimiento equivocado, con la posibilidad de deshacerlo,
> **para** que mis cuentas reflejen solo lo que realmente pasó.

**Reglas de negocio:**
1. Se elimina desde el detalle o deslizando en el historial.
2. Aparece "Movimiento eliminado · Deshacer" durante 5 segundos.
3. La eliminación es lógica (para sincronizar el borrado).
4. Funciona sin conexión.

```gherkin
Escenario: Eliminar y deshacer
  Cuando elimino un gasto de $40.000
  Entonces desaparece del historial y el balance aumenta en $40.000
  Y cuando toco "Deshacer" antes de 5 segundos, el gasto vuelve y el balance se restablece
```

**Fuera de alcance:** papelera de reciclaje, eliminar varios movimientos a la vez.
</example>
</examples>

<stop_conditions>
Antes de redactar, si detectas una contradicción entre decisiones o un dato imprescindible que falta, lístalo como pregunta numerada y espera respuesta. No asumas.
</stop_conditions>

<output_format>
Un único documento Markdown con las secciones numeradas 1 a 4, tablas donde corresponda, y los bloques Gherkin dentro de ```gherkin. Sin texto introductorio ni despedida.
</output_format>

<verification>
Antes de entregar, razona dentro de <thinking> y comprueba, sin incluir el razonamiento en el documento final:
- [ ] Están las 15 historias, con módulo y entrega correctos.
- [ ] Cada historia tiene reglas, Gherkin (≥3 escenarios), casos límite y fuera de alcance.
- [ ] Toda regla indica si funciona sin conexión.
- [ ] Ninguna regla contradice a otra (por ejemplo, HU06 y HU08 sobre cambio de tipo).
- [ ] Los mensajes de pantalla son textos exactos y consistentes entre historias.
</verification>
~~~~

---

## 3. Prompt 2: Arquitectura y base de datos (el CON QUÉ y DÓNDE)

**Objetivo:** producir el stack, estilo arquitectónico, módulos, modelo de datos (servidor y navegador), reglas de sincronización, API y organización del frontend.

~~~~xml
<role>
Eres un arquitecto de software senior con experiencia en sistemas offline-first, sincronización cliente-servidor, PostgreSQL, FastAPI y Angular. Justificas cada decisión técnica con el requisito que la origina, y prefieres la solución más simple que cumpla.
</role>

<context>
Ya existe la especificación funcional de la app de gastos personales (historias, reglas y criterios de aceptación). Ahora debes diseñar la arquitectura que la haga posible. El resultado será la fuente de verdad técnica: los agentes de programación crearán migraciones, endpoints y repositorios a partir de él, así que los nombres de tablas, columnas, tipos y restricciones deben ser exactos.
</context>

<documents>
<document index="1">
<source>Historias de usuario (salida del Prompt 1)</source>
<document_content>
{{SALIDA_PROMPT_1}}
</document_content>
</document>
</documents>

<task>
Redacta las secciones 5 y 6 del Blueprint:
5. Stack tecnológico (tabla: área, tecnología, por qué).
6. Arquitectura:
   6.1 Estilo y diagrama de bloques en ASCII (navegador, API, PostgreSQL, Redis, worker).
   6.2 Módulos del backend y las historias que resuelve cada uno; indica qué historias se resuelven solo en el navegador.
   6.3 Modelo de datos: diagrama ER en Mermaid, columnas comunes de tablas sincronizables, una tabla por entidad del servidor (tipo, restricciones, índices), esquema de la base del navegador, tablas y claves exclusivas del navegador, y las reglas que se calculan con el modelo.
   6.4 API: tabla de endpoints, formato JSON de push y pull, y reglas de sincronización.
   6.5 Frontend: rutas en español, tablas locales y capas por funcionalidad.
</task>

<instructions>
Decisiones técnicas obligatorias (no las reemplaces; si crees que alguna es errónea, dilo en <stop_conditions>):
- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 async + asyncpg, Alembic, PostgreSQL 16+, Redis 7+ con ARQ, Argon2id (pwdlib), PyJWT. Monolito modular con arquitectura hexagonal (api → application → domain ← infrastructure).
- Frontend: Angular ≥ 20 con TypeScript estricto, signals, PWA con service worker, Dexie 4 (IndexedDB), Angular Material, ngx-echarts, uuid v5, cliente generado con ng-openapi-gen.
- Pruebas y calidad: pytest, Vitest + fake-indexeddb, Ruff, mypy, ESLint, Prettier, pre-commit, Docker, GitHub Actions.

Reglas de modelo que debes respetar:
- Dinero en centavos (`amount_minor BIGINT`), con CHECK de rango.
- IDs UUID generados en el cliente; la ocurrencia recurrente usa `uuidv5(fecha ISO, ruleId)`.
- Columnas comunes sincronizables: `id`, `user_id` (lo pone el servidor desde el token), `version` (secuencia global tomada en cada escritura), `created_at` (del dispositivo), `updated_at`, `deleted_at`.
- Unicidad de nombres de categoría con una columna calculada `name_key` (minúsculas, sin tildes), porque `unaccent` no es inmutable en índices.
- Unicidades parciales con `WHERE deleted_at IS NULL`.
- Tablas de acceso (`users`, `refresh_tokens`, `password_reset_tokens`) nunca se sincronizan; los tokens se guardan como hash SHA-256; los refresh tokens usan `family_id` para detectar reutilización.
- La sincronización es push idempotente por `id` + pull paginado por `version`; conflicto = gana el último que llega; los cambios rechazados quedan marcados en el dispositivo; orden de aplicación: categorías → reglas → movimientos → presupuestos.
- En el navegador: cada escritura va a Dexie y al `outbox` en la misma transacción.
- Las recurrencias se generan en el navegador; el servidor solo valida y guarda las reglas.
- Cada decisión del stack se justifica con una frase corta que enlace a un requisito.

Trazabilidad: cada tabla y endpoint debe indicar qué historia (HUxx) lo exige.
</instructions>

<constraints>
- Nada de microservicios, colas adicionales ni tecnologías que ninguna historia requiera (se añade costo sin beneficio).
- No añadas columnas o tablas sin una historia que las justifique.
- Los nombres de código (tablas, columnas, endpoints) en inglés y snake_case en servidor; camelCase en Dexie; rutas del usuario en español.
- Muestra el diagrama Mermaid ER solo con claves y relaciones, y describe el resto en tablas (así el diagrama sigue legible).
- Si una regla de las historias no se puede cumplir con el modelo, no la cambies: repórtala en <stop_conditions>.
</constraints>

<examples>
<example>
**`budgets`: presupuestos (HU14)**

| Columna | Tipo | Regla |
|---|---|---|
| `category_id` | `UUID NOT NULL`, FK a `categories` | Solo categorías de gasto |
| `amount_minor` | `BIGINT NOT NULL` | Límite mensual en centavos. `CHECK (amount_minor > 0)` |
| `effective_from` | `DATE NOT NULL` | Primer día del mes. `CHECK (EXTRACT(DAY FROM effective_from) = 1)` |

Índices: `UNIQUE(user_id, category_id, effective_from) WHERE deleted_at IS NULL` y `(user_id, version)`.
</example>
</examples>

<stop_conditions>
Si una historia exige algo que el modelo no puede soportar, o crees que una decisión obligatoria es errónea, no la resuelvas en silencio: escribe una lista "Contradicciones o riesgos" con la historia afectada y tu recomendación, y pregunta antes de continuar.
</stop_conditions>

<output_format>
Markdown con secciones 5 y 6 numeradas como en <task>. Diagrama ER en bloque ```mermaid y diagrama de bloques en bloque de texto. Tablas para todo lo tabular. Al final, una sección "6.6 Cambios y justificaciones" con las decisiones no obvias y su porqué.
</output_format>

<verification>
Razona en <thinking> (no lo incluyas en la salida) y confirma:
- [ ] Cada historia de la entrada tiene su módulo, tabla o pantalla correspondiente.
- [ ] Cada regla de negocio con efecto en datos tiene columna, restricción o índice que la respalde (por ejemplo: "máx. 5 etiquetas" → CHECK; "sin duplicados de recurrencia" → uuidv5).
- [ ] El diagrama ER coincide con las tablas descritas.
- [ ] Todo funciona sin conexión donde la historia lo exige.
- [ ] Ninguna consulta ni endpoint acepta `user_id` desde el cliente.
</verification>
~~~~

---

## 4. Prompt 3: Cómo deben programar los agentes (el CÓMO)

**Objetivo:** producir la sección 7: el contenido completo de `AGENTS.md` (todas las instrucciones) y `CLAUDE.md` (solo importa `AGENTS.md` y agrega lo propio de Claude Code), para que cualquier agente construya el proyecto con las mismas reglas.

**Entrada que debes pegar:** las salidas de los Prompts 1 y 2 (`{{SALIDA_PROMPT_1}}`, `{{SALIDA_PROMPT_2}}`).
**Salida:** dos bloques de código Markdown listos para copiar a la raíz del repositorio.

~~~~xml
<role>
Eres un ingeniero de plataforma especializado en flujos de trabajo con agentes de programación (Claude Code, Codex, Cursor, Copilot). Sabes escribir archivos AGENTS.md y CLAUDE.md que un agente obedece de forma fiable: cortos, concretos, verificables y con el motivo de cada regla.
</role>

<context>
El proyecto ya tiene su especificación funcional y su arquitectura. Los agentes de IA programarán historia por historia. Si las instrucciones son vagas, extensas o contradictorias, el agente inventa, rompe capas o debilita pruebas. Tu trabajo es traducir la especificación en reglas operativas que un agente pueda seguir y que una persona pueda auditar.
</context>

<documents>
<document index="1">
<source>Historias de usuario (Prompt 1)</source>
<document_content>
{{SALIDA_PROMPT_1}}
</document_content>
</document>
<document index="2">
<source>Arquitectura y modelo de datos (Prompt 2)</source>
<document_content>
{{SALIDA_PROMPT_2}}
</document_content>
</document>
</documents>

<task>
Redacta la sección 7 del Blueprint con:
7.1 El contenido completo de `AGENTS.md`.
7.2 El contenido completo de `CLAUDE.md`.
Incluye antes una tabla que explique qué archivo lee cada herramienta y cómo se mantienen sincronizados.
</task>

<instructions>
`AGENTS.md` debe tener, en este orden:
1. **Contexto:** qué se construye (2-4 líneas) y las fuentes de verdad (`BLUEPRINT.md` = qué, `README.md` = cómo). Si dos documentos se contradicen, el agente pregunta; si AGENTS.md y BLUEPRINT.md difieren, manda BLUEPRINT.md.
2. **Estructura del repositorio:** árbol de carpetas con la ubicación de cada módulo y funcionalidad.
3. **Comandos:** levantar servicios, y los comandos exactos de lint, tipos, pruebas y build de backend y frontend; regenerar el cliente de la API al cambiar un endpoint.
4. **Cómo trabajar una historia:** leer la historia completa → revisar código existente → proponer plan corto → pruebas junto con el código → implementar de adentro hacia afuera (dominio → aplicación → infraestructura → API; dominio → repositorio → página) → ejecutar comandos en verde → reportar.
5. **Reglas que no se rompen**, agrupadas: capas, entre módulos, modelo de datos (dinero en centavos, UUID en cliente, `version` solo del servidor, `name_key`), borrado lógico, seguridad (filtrar siempre por `user_id` del token, `extra="forbid"`, sin secretos ni datos sensibles en logs, sin `bypassSecurityTrust*`), sin conexión (Dexie + outbox en la misma transacción), tiempo (`Clock` inyectado), esquemas (solo migraciones nuevas), pruebas (no debilitar ni borrar), dependencias (no agregar sin preguntar) y alcance (respetar "Fuera de alcance").
6. **Convenciones:** código en inglés; textos de interfaz, comentarios y commits en español; Angular (standalone, OnPush, signals, `inject()`, `@if/@for` con `track`, formularios tipados); Python (type hints, dataclasses, `Protocol`, un caso de uso por clase con `execute`); errores de dominio traducidos a HTTP 422 con `code` y `message`; Conventional Commits con la historia, p. ej. `feat(transactions): registrar gasto sin conexión (HU04)`.
7. **Cuándo detenerse y preguntar:** criterio ambiguo, contradicción entre documentos, cambio al modelo/sincronización/regla del Blueprint, dependencia nueva, prueba existente que falla por algo no tocado.
8. **Formato del reporte final:** historia, cambios por archivo, pruebas nuevas y cobertura, mapa criterio de aceptación → prueba, comandos ejecutados con resultado, pendientes.

`CLAUDE.md` debe contener la línea `@AGENTS.md` (import, para no duplicar reglas) y solo lo propio de Claude Code: usar modo plan antes de cada historia y esperar aprobación; leer solo la sección de la historia (buscar por `#### HUxx`) en vez del Blueprint completo; no hacer commit ni push sin que se pida; si cambia una regla, proponer el cambio en `BLUEPRINT.md` y `AGENTS.md` en lugar de guardarlo solo en la memoria.

Proceso de mantenimiento a documentar: si cambia una regla, primero se corrige el Blueprint; después se copia a `AGENTS.md` en el mismo commit; `CLAUDE.md` casi nunca cambia.
</instructions>

<constraints>
- Cada regla en una línea, imperativa y comprobable, con su motivo cuando no sea obvio (los agentes cumplen mejor lo que entienden).
- Prefiere "haz X" a "no hagas Y" cuando sea posible; reserva las prohibiciones para lo que de verdad no puede romperse.
- No repitas contenido entre `AGENTS.md` y `CLAUDE.md`.
- No copies las historias ni el modelo completo dentro de AGENTS.md: referencia las secciones del Blueprint (el agente carga solo lo que necesita).
- Todos los comandos, rutas y nombres deben coincidir con los de la arquitectura de la entrada; no inventes herramientas nuevas.
- Mantén AGENTS.md por debajo de ~150 líneas útiles; si crece, mueve detalle al README, no a más reglas.
</constraints>

<examples>
<example>
- **Tiempo:** inyecta un `Clock`. Nunca llames a `datetime.now()`, `date.today()` ni `new Date()` dentro del dominio (así las pruebas son deterministas y la regla "no fecha futura" se puede probar).
</example>
</examples>

<stop_conditions>
Si un comando, ruta o regla que necesitas no está en los documentos de entrada, no lo inventes: lístalo en "Datos que faltan" y pregunta.
</stop_conditions>

<output_format>
Sección 7 en Markdown: la tabla introductoria, luego `7.1 AGENTS.md` y `7.2 CLAUDE.md`, cada uno dentro de un bloque de código de cuatro tildes (~~~~markdown) para poder copiarlo tal cual a un archivo.
</output_format>

<verification>
Razona en <thinking> (no lo incluyas en la salida) y confirma:
- [ ] Cada regla de seguridad, sincronización y modelo de la arquitectura tiene su regla operativa en AGENTS.md.
- [ ] Un agente nuevo podría ejecutar los comandos sin preguntar nada.
- [ ] Ninguna regla de AGENTS.md contradice al Blueprint.
- [ ] CLAUDE.md es corto, importa AGENTS.md y no duplica reglas.
- [ ] El formato del reporte permite comprobar que cada criterio de aceptación tiene prueba.
</verification>
~~~~

---

