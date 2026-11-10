# Reportes y discusión del MVP 2

Este documento organiza el **flujo de trabajo con la IA** durante el MVP 2 de voz (HU16–HU19):

- **§1–§2 Reportes de corrección:** ajustes que el equipo pide sobre lo que entregó la IA. No son historias de usuario nuevas: cada uno se plantea como un **prompt de corrección**, con su motivo, lo esperado y el resultado.
- **§3 Discusión:** en orden, lo que pidió el equipo, lo que preguntó o propuso la IA, lo que respondió el equipo y la decisión que quedó.

Fuentes del resultado que se corrige:

| Repositorio | Rama | Commit entregado por la IA | Contenido |
|---|---|---|---|
| BackFinanzas | `dev` | `8bd6fb8` | Módulo `speech` y `POST /speech/token` (HU16), pruebas de HU17–HU19 |
| FrontFinanzas | `dev` | `056c5cf` | Servicios de voz, "Dictar movimiento", "Escuchar movimiento", "Escuchar historial" |

Especificación de referencia: `docs/MVP2.md` (§4 historias, §5 prompts de implementación, §6 implementación realizada).

---

## 1. Registro de correcciones

| ID | Fecha | Área | Hallazgo sobre el resultado de la IA | Tipo | Estado |
|---|---|---|---|---|---|
| C-01 | 2026-11-10 | Frontend (voz) | La voz está repartida en botones por pantalla; no hay un punto de entrada único ni comandos en lenguaje natural, y la confirmación solo se hace tocando "Guardar". | Ajuste funcional y de experiencia | Pendiente |

Estados posibles: **Pendiente** (prompt listo, sin ejecutar), **En curso**, **Aplicada** (con commit) y **Descartada** (con motivo).

---

## 2. C-01 — Asistente de voz global con comandos y confirmación por voz

### 2.1. Resultado entregado por la IA

- El usuario usa la voz en tres lugares separados:
  - "Dictar movimiento": solo en el formulario de nuevo movimiento (HU17).
  - "Escuchar movimiento": solo en el detalle (HU18).
  - "Escuchar historial": solo en la página Movimientos (HU19).
- El dictado solo **prellena** el formulario; el usuario confirma tocando "Guardar".
- No se pueden pedir lecturas filtradas por voz ("léeme los últimos 5 ingresos").

### 2.2. Observación del equipo

> "Es perfecto pero necesitamos que el comando de voz sea más preciso en ciertas cosas. Lo tenemos muy seccionado y así no funciona como me gustaría. Si estoy en cualquier página debería tener un botón flotante para hablarle y decirle cualquier cosa como 'léeme los últimos 5 gastos', 'léeme los últimos 5 ingresos', 'agrega un nuevo gasto de 50000 porque comí en Crepes and Waffles hoy', y que automáticamente, dependiendo de lo que se le diga, haga una acción y lea lo que hizo para uno confirmar si está bien o no, pero todo por voz."

### 2.3. Diagnóstico

| Aspecto | Resultado actual | Lo que se espera |
|---|---|---|
| Punto de entrada | Un botón distinto por pantalla | Un botón flotante en todas las páginas autenticadas |
| Interpretación | Solo entiende frases de registro (parser de HU17) | Reconoce la **intención**: leer últimos N, registrar, confirmar, cancelar, ayuda |
| Lectura | Un movimiento o el historial visible completo | Últimos N gastos, ingresos o todos, pedidos por voz |
| Confirmación | Visual ("Guardar") | Por voz ("¿Lo guardo?" → "sí" / "no"), con alternativa táctil |
| Respuesta | Mensajes en pantalla | La app **dice** lo que hizo y lo muestra |

El ajuste **no cambia** el backend, el modelo de datos ni la sincronización: reutiliza `POST /speech/token`, `TransactionRepo.save` (Dexie + `outbox`) y el dominio de voz ya entregado.

### 2.4. Decisiones del equipo para el ajuste

1. **No se guarda sin confirmación explícita.** El asistente lee el borrador y pregunta "¿Lo guardo?"; silencio, ruido o "no" cancelan. Se conserva así el principio de HU17 (confirmar siempre), ahora también por voz.
2. **"Últimos N":** 5 por defecto, máximo 10 (el mismo bloque de HU19). Sin tipo, lee gastos e ingresos.
3. **Pistas de categoría:** si no se dice el nombre de la categoría, "comí", "almorcé", "cené" y "desayuné" apuntan a Alimentación, y "taxi", "bus" y "gasolina" a Transporte. Si esas categorías no existen, se aplica la regla de HU17.
4. **Los botones actuales se mantienen** como accesos directos; el botón flotante es el acceso global.
5. **Una sola pregunta de seguimiento:** si falta el monto, el asistente pregunta una vez; si sigue sin entender, abre el formulario prellenado.
6. **Sigue fuera del ajuste:**
   - Editar o eliminar por voz.
   - Palabra de activación siempre escuchando.
   - Interrumpir al asistente mientras habla.
   - Consultas de presupuestos o gráficos.

### 2.5. Prompt de corrección

```xml
<role>
Eres un ingeniero frontend senior experto en Angular 22 (standalone, OnPush, signals, `inject()`), PWAs offline-first con Dexie, interfaces de voz y accesibilidad (WCAG 2.2). Corriges un resultado ya entregado sin romper lo que funciona y sigues `AGENTS.md`.
</role>

<context>
Repositorio FrontFinanzas, rama `dev`. En el commit `056c5cf` entregaste las funciones de voz del MVP 2 (HU16–HU19, ver `BackFinanzas/docs/MVP2.md` §6.6). El equipo las revisó y pide una corrección (C-01 en `BackFinanzas/docs/REPORTES-Y-DISCUSION.md`): la voz quedó repartida en botones por pantalla y debe funcionar como un asistente único.

Observación textual del equipo:
"Si estoy en cualquier página debería tener un botón flotante para hablarle y decirle cualquier cosa como 'léeme los últimos 5 gastos', 'léeme los últimos 5 ingresos', 'agrega un nuevo gasto de 50000 porque comí en Crepes and Waffles hoy', y que automáticamente, dependiendo de lo que se le diga, haga una acción y lea lo que hizo para uno confirmar si está bien o no, pero todo por voz."

Lo que ya existe y DEBES reutilizar (no dupliques):
- `src/app/core/speech/`: `SpeechAuthService`, `SpeechRecognitionService` (`listen()`, `state`), `SpeechSynthesisService` (`speakOne`, `playQueue`, `stop`, exclusividad), puerto `SpeechEngine` y `speech-errors.ts` (`SpeechError`, `SPEECH_TEXT`, `speechMessage`).
- `src/app/features/movimientos/domain/voice.ts`: `parseVoiceTransactionDraft`, `formatTransactionForSpeech`, `buildHistorySpeechQueue`, `normalizeSpeech`.
- `TransactionRepo` (`save`, `lastUsedCategory`, `visible`), `CategoryRepo` (`active`, `byId`), `BudgetRepo.alertsAfterSave`, `SyncService` (`sync`, `offline`), `AuthService.currency`, `Clock`.
- Shell de las páginas autenticadas: `src/app/layout/shell.ts` y `shell.html`.
</context>

<task>
Corrige la experiencia de voz entregada: añade un asistente de voz flotante, disponible en toda la app autenticada, que reconozca la intención de lo que dice el usuario, ejecute la acción, responda en voz alta lo que hizo y pida confirmación por voz antes de guardar. Mantén funcionando los botones de voz actuales.
</task>

<instructions>
1. **Dominio puro** — `src/app/features/asistente/domain/intents.ts`, sin Angular, Dexie ni SDK. La fecha de hoy llega por parámetro desde `Clock`.
   - `parseVoiceIntent(transcript, categories, today, lastUsed)` devuelve una unión discriminada:

     | Intención | Frases de ejemplo | Resultado |
     |---|---|---|
     | `read_last` | "léeme los últimos 5 gastos", "dime mis últimos ingresos", "qué fue lo último que gasté" | `{ type: 'expense' \| 'income' \| 'all', count }` (5 por defecto, máximo 10, mínimo 1) |
     | `create` | "agrega un nuevo gasto de 50000 porque comí en Crepes and Waffles hoy", "registra un ingreso de dos millones de salario" | `{ draft }` usando `parseVoiceTransactionDraft` y las pistas de categoría por verbo |
     | `confirm` | "sí", "confirmo", "guárdalo", "está bien" | — |
     | `cancel` | "no", "cancela", "déjalo así" | — |
     | `help` | "qué puedo decir", "ayuda" | — |
     | `unknown` | cualquier otra | — |

   - Pistas de categoría: "comí", "almorcé", "cené", "desayuné" → Alimentación; "taxi", "bus", "gasolina" → Transporte, solo si existen y están activas. Si no, la regla actual de HU17.
   - `describeDraftForConfirmation(...)`, por ejemplo: "Voy a registrar un gasto de $50.000 en Alimentación, hoy, concepto: Crepes and Waffles. ¿Lo guardo?"
   - `buildLastTransactionsSpeech(...)`: "Tus últimos 5 gastos: …", reutilizando `formatTransactionForSpeech`; si no hay, "No tienes gastos registrados".
2. **Orquestador** — `src/app/features/asistente/data/voice-assistant.service.ts`:
   - Máquina de estados con signals: `idle → listening → processing → speaking → awaiting_confirmation → saving → idle`.
   - Tras leer el borrador, escucha **una** respuesta. Solo `confirm` guarda; silencio, ruido o `cancel` responden "No lo guardé" y no persisten nada.
   - Si falta el monto, pregunta una vez "¿De cuánto fue el gasto?"; si sigue sin entenderlo, abre `/movimientos/nuevo` con el borrador prellenado.
   - Guarda con `TransactionRepo.save`, luego `BudgetRepo.alertsAfterSave` y `SyncService.sync()`; dice "Gasto guardado" o "Ingreso guardado" y las alertas.
   - Expone `state`, `transcript` y `reply`; `cancel()` corta todo y libera el micrófono; cambiar de ruta cancela.
3. **UI** — `src/app/features/asistente/components/voice-assistant-fab.ts`, montado en el shell:
   - Botón flotante con `aria-label="Asistente de voz"`, estados visibles y `aria-live`. Oculto en login, registro y recuperación; no tapa la navegación inferior en móvil.
   - Panel compacto con lo que escuchó, lo que entendió y la respuesta, y botones "Confirmar" y "Cancelar" como alternativa táctil.
   - Respeta `prefers-reduced-motion` y los tokens de color de `styles.scss`.
4. **Integración:** abrir el asistente detiene cualquier lectura de HU18/HU19 y viceversa. "Dictar movimiento", "Escuchar movimiento" y "Escuchar historial" siguen igual.
5. **Documentación:**
   - En `BackFinanzas/docs/MVP2.md` añade §6.7 "Ajuste C-01: asistente de voz global", con lo cambiado y la nota de que HU17/HU19 ahora también admiten confirmación por voz y lectura filtrada a través del asistente.
   - En `BackFinanzas/docs/REPORTES-Y-DISCUSION.md` completa §2.6 "Resultado de la corrección" y cambia el estado de C-01.
</instructions>

<constraints>
- Es una corrección, no una historia nueva: no crees HU20 ni cambies la numeración de `docs/MVP2.md`.
- Sin dependencias nuevas, sin LLM ni servicios externos: la interpretación es determinista y local.
- Sin cambios en el backend, el modelo de datos, Dexie, el `outbox` ni `POST /speech/token`.
- Nunca guardar sin confirmación explícita (voz o toque).
- Sin conexión: el botón informa "Los servicios de voz requieren conexión a internet" y no abre el micrófono; el uso manual offline queda intacto.
- Los componentes no usan `HttpClient`, Dexie ni el SDK directamente.
</constraints>

<tests>
- `intents.spec.ts`:
  - Las tres frases del equipo.
  - Montos hablados y en cifras.
  - N: por defecto, mayor que 10 y 0.
  - Sinónimos de confirmar y cancelar.
  - "Comí" → Alimentación.
  - Frase desconocida.
- `voice-assistant.service.spec.ts`, con el `SpeechEngine` falso:
  - "léeme los últimos 5 gastos" lee 5 gastos.
  - Crear → leer borrador → "sí" → guarda en Dexie + outbox y dice "Gasto guardado".
  - "no" y silencio no guardan.
  - Falta el monto → una pregunta.
  - Sin conexión.
  - Micrófono denegado.
  - Cambiar de ruta cancela.
- Prueba de componente del FAB: visible en rutas autenticadas y oculto en `/login`.
- Las pruebas actuales de voz (HU16–HU19) siguen en verde sin modificarlas.
</tests>

<stop_conditions>
Detente y pregunta si el ajuste exige tocar el backend o el modelo de datos, si necesitas una dependencia nueva, si una prueba existente falla por algo que no tocaste, o si una conversación típica pudiera superar la cuota de 30 tokens por hora.
</stop_conditions>

<workflow>
1. Lee este reporte, `docs/MVP2.md` §4.3 y §6.6, y el código indicado.
2. Presenta un plan corto por capa y espera aprobación.
3. Implementa dominio → servicio → componente, con sus pruebas.
4. Ejecuta `npm run lint`, `npm test` y `npm run build` (Node ≥ 22.22.3) y déjalos en verde.
</workflow>

<output_format>
Reporte con el formato de `AGENTS.md`: Corrección C-01, Cambios, Pruebas, Escenario → prueba que lo verifica, Comandos y resultado, Pendientes. Incluye una tabla con cada frase probada y lo que respondió el asistente.
</output_format>

<verification>
- [ ] Botón flotante en todas las páginas autenticadas y en ninguna de autenticación.
- [ ] Las tres frases del equipo funcionan de punta a punta en las pruebas.
- [ ] Ningún guardado sin confirmación; el guardado pasa por `TransactionRepo.save`.
- [ ] Los botones de voz anteriores siguen funcionando y sus pruebas no cambiaron.
- [ ] `MVP2.md` §6.7 y `REPORTES-Y-DISCUSION.md` §2.6 actualizados.
- [ ] lint, test y build en verde.
</verification>
```

### 2.6. Resultado de la corrección

_Pendiente de ejecutar el prompt. Al aplicarlo, registrar aquí:_

| Campo | Valor |
|---|---|
| Fecha de ejecución | |
| Herramienta / modelo | |
| Commit | |
| Frases probadas y respuesta del asistente | |
| Pruebas (nuevas / totales) | |
| Desviaciones respecto al prompt y su motivo | |
| Estado final de C-01 | |

---

## 3. Discusión: preguntas de la IA y decisiones del equipo

Registro en orden cronológico de la sesión del 2026-11-10 (Claude Code, modelo Claude Opus 5.5). Las solicitudes y respuestas del equipo se citan textualmente.

### 3.1. Resumen de decisiones

| # | Etapa | Pregunta o propuesta de la IA | Decisión del equipo | Dónde quedó |
|---|---|---|---|---|
| D-01 | Prompts por HU | Los prompts cubren solo el backend; ¿generar también una versión para FrontFinanzas? | No se pidió aparte: el equipo pasó a implementar y luego pidió el frontend (D-05). | `MVP2.md` §5 |
| D-02 | Implementación backend | `httpx` (cliente HTTP para Azure) solo está como dependencia de desarrollo. ¿Moverla a ejecución o usar solo la biblioteca estándar? | **Mover `httpx` a dependencias de ejecución** (recomendada). | `pyproject.toml`, `uv.lock` |
| D-03 | Implementación backend | No hay `uv`, Docker, PostgreSQL ni Redis en la máquina. ¿Cómo verificar? | **Instalar `uv` y verificar parcialmente** (recomendada); las pruebas con BD y Redis quedan para la CI. | `MVP2.md` §6.5 |
| D-04 | Implementación backend | Plan de implementación HU16–HU19 (modo plan, como exige `CLAUDE.md`). | **Plan aprobado** sin cambios. | Commit `8bd6fb8` |
| D-05 | Revisión del backend | Dos decisiones por revisar: (a) ¿un intento que termina en 503 consume cuota? (b) ¿aplicar en `AGENTS.md`/`BLUEPRINT.md` la regla de errores 401/429/503? | **Tomar la opción recomendada y más profesional:** el 503 sí consume cuota y la regla se aplica. Además: **seguir con el frontend**. | `AGENTS.md`, `BLUEPRINT.md`, `MVP2.md` §6.4 |
| D-06 | Publicación | (Sin pregunta) | **Commit y push en `dev`** de backend y frontend. | Commits `8bd6fb8` y `056c5cf` |
| D-07 | Evaluación con la rúbrica | Faltantes frente a la rúbrica y oferta de completar la documentación. | Se dejó en espera: el equipo priorizó corregir la experiencia de voz (D-08). | §3.2, etapa 6 |
| D-08 | Ajuste de la voz | Convertir el pedido del asistente global en dos prompts: especificar una **HU20** e implementarla. | **No es una HU nueva, es una corrección** al resultado entregado; crear un reporte de correcciones. | §2 (C-01) |
| D-09 | Organización | ¿Subir el reporte a `dev` o ejecutar ya el prompt de C-01? | Primero **documentar las preguntas y decisiones** y renombrar el documento a "reportes y discusión". | Este documento |

### 3.2. Detalle por etapa

#### Etapa 1 — Prompts de implementación por historia

- **Solicitud del equipo:** "genera un prompt con ingenieria de prompts para implementar cada una de las historias de usuario que se encuentran en el archivo MVP2.md de la carpeta docs en la rama dev ( con los nombres hu16, hu17, hu18, hu19 ) en el proyecto de backFinanzas, aclaracion: es un prompt por cada historia de usuario y estos prompts guardarlos en el mismo archivo MVP2.md"
- **Lo que hizo la IA:** cuatro prompts en formato XML (rol, contexto, tarea, restricciones, pruebas, condiciones de parada y verificación), guardados en `MVP2.md` §5.
- **Lo que advirtió o propuso la IA:**
  - BackFinanzas solo contiene el backend, así que HU17–HU19 quedan en el servidor como pruebas de contrato y regresión.
  - `httpx` está solo como dependencia de desarrollo.
  - Ofreció una versión de los prompts para el frontend (D-01).

#### Etapa 2 — Implementación del backend

- **Solicitud del equipo:** "ahora utiliza cada uno de los prompts hechos para las historias de usuario, para implementar cada uno, documenta de manera general lo desarrollado en estas historias de usuario."
- **Preguntas de la IA y respuestas del equipo:**

  | Pregunta de la IA | Opciones presentadas | Respuesta del equipo |
  |---|---|---|
  | "Para llamar al STS de Azure (HU16) el backend necesita un cliente HTTP. `httpx` ya está en uv.lock pero solo como dependencia de desarrollo; AGENTS.md exige autorización para dependencias. ¿Qué hago?" | Mover httpx a runtime (recomendada) · Usar solo la biblioteca estándar | "Mover httpx a runtime (Recommended)" |
  | "En esta máquina no hay `uv`, ni Docker, ni PostgreSQL (5433) / Redis (6380) levantados, así que las pruebas de integración/aceptación no pueden correr aquí. ¿Cómo verifico?" | Instalar uv y verificar parcial (recomendada) · El equipo levanta Docker · No instalar nada | "Instalar uv y verificar parcial (Recommended)" |
  | Plan de implementación por capas (modo plan) | Aprobar o ajustar | Plan aprobado |

- **Resultado:** módulo `speech` con `POST /speech/token`, pruebas, `openapi.json` y documentación en `MVP2.md` §6.
- **Decisiones que la IA dejó para revisar:**
  1. Un intento que termina en 503 consume cuota.
  2. Propuesta de ampliar la regla de errores HTTP en `AGENTS.md` y `BLUEPRINT.md`.

#### Etapa 3 — Decisiones pendientes e implementación del frontend

- **Solicitud del equipo:** "en cuanto a las decisiones que conviene revisar toma la opcion recomandada y que se mas profesional, ademas de eso sigue con la parte de interfaz del frontend para que quede integrado con el frontend que ya tenemos en el proyecto"
- **Decisiones aplicadas:**
  - El 503 sigue consumiendo cuota.
  - La regla "errores de dominio → 422, salvo 401/429/503" quedó escrita en `AGENTS.md` y `BLUEPRINT.md`.
- **Resultado:** interfaz de voz en FrontFinanzas: "Dictar movimiento", "Escuchar movimiento", "Escuchar historial" y la barra de lectura (`MVP2.md` §6.6).
- **Lo que advirtió la IA:** el CLI de Angular 22 exige Node ≥ 22.22.3 y la máquina tiene 22.19.0. Para verificar se usó `npx -p node@24`.

#### Etapa 4 — Publicación

- **Solicitud del equipo:** "sube los cambios, haz el commit y el push correcto en la rama dev, tanto en el backend como en el frontend"
- **Resultado:**
  - Commits `8bd6fb8` (BackFinanzas) y `056c5cf` (FrontFinanzas) en `dev`, con Conventional Commits en español.
  - Antes de subir se repitieron las verificaciones y se revisó que no hubiera secretos.

#### Etapa 5 — Revisión con la rúbrica

- **Solicitud del equipo:** "dime si lo hecho y lo que ya tenemos cumple con la rubrica, que se encuentra en :"C:\Users\ASUS\Desktop\RUBRICA DE EVALUACION-Taller2-MVP2.pdf" o que le faltaria para tener en cuenta"
- **Respuesta de la IA:**
  - Cumple: historias de usuario, uso del SDK y control de versiones.
  - Faltan: lecciones aprendidas, registro ordenado de prompt → respuesta, prueba real con Azure, plan por Sprints, capturas de la interfaz, README actualizados y material de presentación.
- **Oferta de la IA:** completar la documentación faltante (D-07, en espera).

#### Etapa 6 — Ajuste de la experiencia de voz

- **Solicitud del equipo:** "aplicando ingenieria de prompts nuevamente todo este texto transformalo a como deberia ser un prompt, si te parece que serian varios prompts diferentes hazlo tambien y dimelo en el texto, el texto es el siguiente: es perfecto pero necesitamos que el comando de voz sea mas preciso en ciertas cosas, por ejemplo, lo tenemos muy seccionado y asi no funciona como me gustaria, por ejemplo si estoy en cualquier pagina yo deberia de tener un boton flotante para hablarle y decirle cualquier cosa como "leeme los ultimos 5 gastos" "leeme los ultimos 5 ingresos" "agrega un nuevo gasto de 50000 porque comi en crepes and waffles hoy" y que esta automaticamente dependiendo lo que se le diga haga una accion y lea automaticamente lo que hizo para uno confirmar si esta bien o no pero todo por voz"
- **Propuesta de la IA:**
  - Dos prompts: (1) especificar una HU20 "Asistente de voz global" y (2) implementarla en FrontFinanzas.
  - Ningún prompt para el backend.
  - Decisiones para resolver ambigüedades:
    - Confirmar por voz antes de guardar.
    - N = 5 por defecto y como máximo 10.
    - Pistas de categoría por verbo ("comí" → Alimentación).
    - Mantener los botones actuales.

#### Etapa 7 — Reencuadre como corrección

- **Solicitud del equipo:** "crea un documento llamado reporte pero este contiene los cambios que vamos a hacer con el resultado que me diste hace rato, es decir correciones o ajuste al resultado de la ia, entonces ese prompt que hiciste no puede ser una historia de usuario si no como un prompt de correcion a lo que nos entregaste"
- **Resultado:**
  - El pedido quedó como **corrección C-01** (§2), con un único prompt de corrección.
  - Ese prompt prohíbe crear la HU20 y exige conservar lo ya entregado y sus pruebas.
- **Preguntas de la IA:** ¿subir el documento a `dev` o ejecutar el prompt de C-01? (D-09)

#### Etapa 8 — Organización del flujo de trabajo

- **Solicitud del equipo:** "listo a ese documento necesito que le agregues todas las preguntas que me hiciste y la decision que tomé esto para tener organizado como fue el flujo de trabajo, es decir lo que preguntabas y lo que yo decia, que este organizado y cambia el nombre del documento de reporte a: reportes y discusion"
- **Resultado:** este documento, renombrado a `REPORTES-Y-DISCUSION.md`, con la sección §3.

### 3.3. Decisiones que tomó la IA sin consulta previa (para validar)

| Decisión | Motivo | Riesgo / cómo revertir |
|---|---|---|
| Agregar `microsoft-cognitiveservices-speech-sdk` al frontend | Es el SDK obligatorio definido en `MVP2.md` §3; sin él no hay voz. | Ninguno; ya estaba aprobado en la especificación. |
| Cargar el SDK desde su bundle oficial para navegador | La entrada principal del paquete arrastra módulos de Node (`https`, `url`) y el build fallaba. | Si el SDK cambia la ruta del bundle, ajustar `azure-speech-engine.ts` y `angular.json`. |
| Asociar el token de voz a la cuenta activa | Evita reutilizar el token de otra sesión en el mismo navegador. | Ninguno funcional; es una medida de seguridad adicional. |
| Verificar el frontend con Node 24 vía `npx` | El CLI de Angular 22 no corre con Node 22.19.0. | El equipo debe actualizar Node para usar `npm run lint/test/build` directamente. |
| Instalar `uv` con `pip --user` y crear `backend/.venv` | Necesario para correr ruff, mypy y pytest (D-03). | `.venv` está ignorado por git. |
