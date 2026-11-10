# MVP 2: Ampliación con Servicios de Voz

## 1. Contexto y relación con el MVP 1

El **MVP 1** consolidó la base funcional y arquitectónica de la aplicación web progresiva (PWA) de finanzas personales con funcionamiento sin conexión:

- **Frontend (Angular + Dexie/IndexedDB):** gestión local de movimientos, categorías, reglas recurrentes, presupuestos, gráficos y cola de salida (`outbox`) para sincronización diferida.
- **Backend (FastAPI + PostgreSQL + Redis):** arquitectura hexagonal modular (`auth`, `categories`, `transactions`, `recurring`, `budgets`, `sync`) con autenticación JWT, validaciones de dominio y sincronización incremental (`push`/`pull`).

El **MVP 2** se plantea como una ampliación incremental sobre la base del MVP 1 orientada a incorporar **interacción por voz bidireccional** en el módulo de movimientos (`transactions`). El propósito es reducir la fricción al registrar gastos e ingresos y ofrecer una alternativa auditiva para consultarlos, sin alterar las reglas de negocio, el modelo de datos ni las garantías de persistencia y sincronización ya establecidas.

---

## 2. Objetivos del MVP 2

### Objetivo general

Integrar servicios de reconocimiento y síntesis de voz en la aplicación para que el usuario pueda registrar movimientos mediante dictado y escuchar la lectura de sus movimientos registrados de manera ágil, accesible y coherente con la arquitectura del MVP 1.

### Objetivos específicos

1. **Registro de movimientos mediante voz (Speech-to-Text):**
   - Permitir al usuario iniciar una captura por voz desde la interfaz para dictar gastos o ingresos de forma natural.
   - Transcribir el audio del usuario e interpretar o estructurar los datos clave del movimiento (tipo, monto, categoría, fecha y descripción) para prellenar o confirmar el registro antes de persistirlo.
   - Mantener intacto el flujo offline-first una vez capturado el movimiento: validación de dominio (`amount_minor` entero en centavos, categoría válida) y almacenamiento conjunto en Dexie y en el `outbox`.

2. **Lectura de movimientos al usuario (Text-to-Speech):**
   - Habilitar la reproducción en voz alta de los movimientos registrados (detalle de un movimiento o lectura de elementos del historial/consulta).
   - Presentar la información financiera de forma clara y natural en español (tipo de movimiento, monto con la moneda configurada, categoría, fecha y descripción), mejorando la accesibilidad y permitiendo una consulta manos libres.

3. **Integración segura y resiliente con la arquitectura existente:**
   - Respetar la separación de capas (servicios/adaptadores de voz desacoplados del dominio y de los componentes visuales).
   - Evitar la exposición de secretos o claves de suscripción en el código cliente (`environment.ts`), gestionando la autorización del servicio de voz mediante credenciales temporales emitidas por el backend.
   - Garantizar una degradación controlada ante ausencia de conexión o permisos de micrófono denegados, conservando plenamente operativas las funciones manuales y offline del MVP 1.

---

## 3. Definición del SDK a usar

Para implementar las capacidades de voz del MVP 2 se utilizará el SDK oficial de Microsoft Azure AI Speech para JavaScript/TypeScript:

- **Paquete / SDK:** `microsoft-cognitiveservices-speech-sdk`
- **Proveedor de servicio:** Azure AI Speech (Cognitive Services)

### Capacidades del SDK a emplear

| Capacidad | Uso en el MVP 2 | Componentes principales del SDK |
|---|---|---|
| **Reconocimiento de voz (STT - Speech-to-Text)** | Captura de audio desde el micrófono del navegador y transcripción a texto en español para el registro de movimientos por voz. | `SpeechConfig`, `AudioConfig` (micrófono), `SpeechRecognizer` |
| **Síntesis de voz (TTS - Text-to-Speech)** | Conversión de texto a audio hablado en voz natural en español para leer al usuario sus movimientos registrados. | `SpeechConfig`, `AudioConfig` (altavoz/salida de audio), `SpeechSynthesizer` |

### Lineamientos técnicos de integración

- **Ubicación en el frontend:** El SDK `microsoft-cognitiveservices-speech-sdk` se integrará en la aplicación Angular encapsulado detrás de un servicio o adaptador dedicado, evitando que los componentes de UI interactúen directamente con los detalles de bajo nivel del SDK.
- **Autenticación y seguridad:** De acuerdo con las políticas de seguridad del proyecto, la clave de suscripción (`Speech Key`) no debe residir en el frontend. El cliente obtendrá un token de autorización temporal (y la región correspondiente) a través de un endpoint protegido del backend autenticado con la sesión del usuario, inicializando el SDK con dicho token.
- **Dependencia de conectividad:** Al tratarse de un servicio cognitivo en la nube, el reconocimiento y la síntesis mediante `microsoft-cognitiveservices-speech-sdk` requieren conexión a internet y permisos de micrófono (para STT) en el navegador. Si el usuario se encuentra sin conexión, la interfaz informará la indisponibilidad del servicio de voz y mantendrá habilitado el registro y la consulta manual offline del MVP 1.

## Primer prompts para HU
<role>
Eres un analista de producto senior especializado en aplicaciones de finanzas personales y experiencias accesibles por voz, con amplia experiencia redactando historias de usuario en formato Connextra, reglas de negocio verificables y criterios de aceptación en Gherkin. Escribes en español claro, preciso y sin ambigüedades.
</role>

<context>
Contamos con el MVP 1 de una app web progresiva (PWA) de finanzas personales que funciona sin conexión (Angular + Dexie/IndexedDB en frontend y FastAPI + PostgreSQL en backend, con sincronización mediante outbox). Ahora vamos a especificar el MVP 2 como una ampliación sobre el MVP 1 para incorporar servicios de voz bidireccionales mediante el SDK `microsoft-cognitiveservices-speech-sdk`: registrar movimientos por voz (Speech-to-Text) y leer los movimientos al usuario (Text-to-Speech).

Este resultado servirá como fuente de verdad funcional para agentes de arquitectura y programación; por ello, cada regla debe ser comprobable y consistente con el MVP 1.
</context>

<documents>
<document index="1">
<source>docs/MVP2.md</source>
<document_content>
{{PEGA_AQUI_EL_CONTENIDO_DE_docs/MVP2.md}}
</document_content>
</document>
<document index="2">
<source>BLUEPRINT.md (secciones de referencia del MVP 1: conceptos base, HU04–HU07, HU11 y modelo de datos de movimientos)</source>
<document_content>
{{PEGA_AQUI_LAS_SECCIONES_RELEVANTES_DE_BLUEPRINT.md}}
</document_content>
</document>
</documents>

<task>
Redacta la especificación funcional de las historias de usuario necesarias para implementar el MVP 2 (ampliación de servicios de voz sobre el MVP 1), incluyendo:
1. Un mapa inicial de historias del MVP 2 (Módulo, HU iniciando en HU16, Título, Prioridad MoSCoW y Dependencia con el MVP 1).
2. El detalle completo de cada historia de usuario necesaria para cubrir:
   - Registro de gastos e ingresos mediante voz (Speech-to-Text con `microsoft-cognitiveservices-speech-sdk`), interpretación de datos del movimiento y confirmación antes de guardar.
   - Lectura en voz alta de movimientos individuales o del historial/listado al usuario (Text-to-Speech con `microsoft-cognitiveservices-speech-sdk`), con controles de reproducción.
   - Autorización segura del servicio de voz (obtención de token temporal desde el backend sin exponer claves en el cliente) y manejo de permisos de micrófono/conectividad, si aplica como historia independiente o integrada.
</task>

<instructions>
Cada historia de usuario debe redactarse obligatoriamente en **formato Connextra** y seguir esta estructura fija en orden:
a) Encabezado `#### HUxx. Título` (numeración consecutiva desde `HU16`).
b) Declaración en **formato Connextra** dentro de un bloque de cita:
   > **Como** [rol o perfil de usuario],
   > **quiero** [funcionalidad o acción concreta],
   > **para** [beneficio o valor esperado].
c) Contexto (1-2 frases explicando qué aporta sobre el flujo actual del MVP 1).
d) Reglas de negocio numeradas. Usa tablas cuando definas campos extraídos, comandos o formatos de lectura. Indica siempre el comportamiento con conexión y sin conexión.
e) Criterios de aceptación en Gherkin en español (`Escenario / Dado / Cuando / Entonces / Y`) con valores concretos (montos en moneda del usuario, fechas, categorías y textos exactos de interfaz o locución).
f) Casos límite (permiso de micrófono denegado, audio vacío o no entendido, monto/categoría ambigua, pérdida de conexión durante el dictado o lectura, doble clic, interrupción de reproducción).
g) Fuera de alcance, explícito.

Decisiones del MVP 1 y MVP 2 que debes respetar sin alterarlas:
- SDK obligatorio: `microsoft-cognitiveservices-speech-sdk` (Azure AI Speech) para STT y TTS en español.
- Dinero: los montos se guardan siempre como enteros en centavos (`amount_minor`), usando la moneda configurada en la cuenta del usuario (por defecto COP).
- Persistencia sin conexión: una vez confirmado el movimiento dictado por voz, se valida con las mismas reglas de HU04/HU05 y se guarda en Dexie + `outbox` en una única transacción.
- Seguridad: nunca se almacenan claves de suscripción de Azure Speech en el frontend ni en `environment.ts`; el cliente solicita un token temporal al backend usando su sesión autenticada.
- Conectividad: los servicios cognitivos de voz requieren internet; sin conexión, las acciones de voz deben informar claramente su indisponibilidad sin bloquear el registro ni la consulta manual offline del MVP 1.
</instructions>

<constraints>
- Todas las historias deben usar estrictamente el formato Connextra (`Como / quiero / para`) y responder a una necesidad observable del usuario.
- Cada regla de negocio debe ser verificable mediante una prueba automatizada.
- Incluye como mínimo 4 escenarios Gherkin por historia: camino feliz, error de entrada o ambigüedad, fallo de permisos o servicio, y escenario sin conexión.
- Usa textos exactos de mensajes en pantalla y ejemplos reales de frases dictadas y leídas (nunca placeholders genéricos como "un texto" o "un monto").
- No modifiques ni redefinas reglas ya cerradas en HU01–HU15 de `BLUEPRINT.md`.
- Lo que no sea imprescindible para el MVP 2 (por ejemplo, conversaciones multi-turno complejas, wake-word en segundo plano, comandos para editar presupuestos o soporte sin conexión mediante modelos locales) debe quedar explícitamente en "Fuera de alcance".
</constraints>

<examples>
<example>
#### HU16. Registrar movimiento por dictado de voz

> **Como** usuario de la app de finanzas personales,
> **quiero** dictar un gasto o ingreso usando el micrófono y revisar los datos interpretados antes de guardarlo,
> **para** registrar mis movimientos en segundos sin tener que escribir manualmente en el formulario.

**Contexto:** amplía el registro rápido de HU04 y HU05 incorporando captura por voz mediante `microsoft-cognitiveservices-speech-sdk`, manteniendo las mismas validaciones de dominio y el guardado en Dexie/outbox.

**Reglas de negocio:**
1. El botón "Dictar movimiento" solo está habilitado cuando hay conexión a internet; sin conexión muestra el aviso "El registro por voz requiere conexión a internet".
2. Al activar el dictado, la app solicita permiso de micrófono si aún no fue concedido y obtiene un token temporal de voz del backend.
3. El texto transcrito se analiza para prellenar tipo (`gasto` o `ingreso`), monto, categoría coincidente y descripción; el usuario siempre debe confirmar antes de persistir.
4. Si falta algún campo obligatorio o hay ambigüedad (por ejemplo, el monto o la categoría), el formulario se abre con lo reconocido y resalta los campos pendientes para completarlos manualmente.
5. Al confirmar, el movimiento se almacena como entero en centavos (`amount_minor`) en Dexie junto con su entrada en `outbox` dentro de la misma transacción.

```gherkin
Escenario: Registrar un gasto exitoso mediante dictado de voz
  Dado que tengo conexión a internet y permiso de micrófono concedido
  Cuando presiono "Dictar movimiento" y digo "Gasté veinticinco mil pesos en almuerzo en Alimentación"
  Entonces veo el formulario prellenado con tipo "Gasto", monto "$25.000", categoría "Alimentación" y descripción "Almuerzo"
  Y al presionar "Guardar movimiento" se registra en IndexedDB y se encola en el outbox para sincronizar

Escenario: Intento de dictado sin conexión a internet
  Dado que el dispositivo se encuentra sin conexión
  Cuando intento usar la opción "Dictar movimiento"
  Entonces veo el mensaje "El registro por voz requiere conexión a internet"
  Y permanece disponible el registro manual sin conexión
```

**Casos límite:** permiso de micrófono denegado, silencio prolongado o audio ininteligible, monto negativo o cero dictado, doble pulsación sobre el botón de micrófono.

**Fuera de alcance:** guardado automático sin confirmación previa del usuario, comandos de voz para editar o eliminar movimientos existentes.
</example>
</examples>

<stop_conditions>
Antes de redactar, si detectas una contradicción con `BLUEPRINT.md` o `docs/MVP2.md`, o si falta una definición imprescindible (por ejemplo, si el usuario podrá confirmar por voz o solo mediante botón en pantalla, o el idioma/acento objetivo del SDK), detente, enumera las preguntas concretas y espera respuesta. No asumas decisiones no documentadas.
</stop_conditions>

<output_format>
Entrega un único documento Markdown listo para anexar o integrar en `docs/MVP2.md` o en el Blueprint, con:
1. Tabla resumen (Mapa de historias del MVP 2).
2. Sección detallada con cada historia `HU16` en adelante y sus bloques ```gherkin.
Sin texto introductorio ni despedida.
</output_format>

<verification>
Antes de entregar, razona dentro de `<thinking>` (sin incluir ese razonamiento en la respuesta final) y verifica:
- [ ] Todas las historias usan el formato Connextra (`Como / quiero / para`) en bloque de cita.
- [ ] Las historias cubren tanto Speech-to-Text (registro) como Text-to-Speech (lectura de movimientos) usando `microsoft-cognitiveservices-speech-sdk`.
- [ ] Cada historia incluye al menos 4 escenarios Gherkin concretos con textos y montos reales.
- [ ] Se respeta el manejo monetario en `amount_minor`, el flujo Dexie + outbox y la no exposición de secretos en el frontend.
- [ ] El comportamiento sin conexión está explicitado en todas las historias.
</verification>


## Refinados y tareas tecnicas - Respuestas

<role>
Eres un analista de producto y arquitecto técnico senior especializado en aplicaciones de finanzas personales y experiencias accesibles por voz. Dominas la redacción de historias de usuario en formato Connextra, reglas de negocio verificables, criterios de aceptación en Gherkin, priorización MoSCoW, estimación de esfuerzo y descomposición en tareas técnicas por capas (FastAPI hexagonal y Angular PWA offline-first). Escribes en español claro, preciso y sin ambigüedades.
</role>

<context>
Contamos con el MVP 1 de una app web progresiva (PWA) de finanzas personales que funciona sin conexión (Angular + Dexie/IndexedDB en frontend y FastAPI + PostgreSQL en backend, con sincronización mediante outbox). Ahora vamos a especificar el MVP 2 como una ampliación sobre el MVP 1 para incorporar servicios de voz bidireccionales mediante el SDK `microsoft-cognitiveservices-speech-sdk`: registrar movimientos por voz (Speech-to-Text) y leer los movimientos al usuario (Text-to-Speech).

Este resultado servirá como fuente de verdad funcional y de planificación técnica para los agentes que implementarán el código; por ello, cada historia debe incluir su clasificación, prioridad, estimación y tareas técnicas derivadas de forma consistente con el MVP 1.
</context>

<documents>
<document index="1">
<source>docs/MVP2.md</source>
<document_content>
{{PEGA_AQUI_EL_CONTENIDO_DE_docs/MVP2.md}}
</document_content>
</document>
<document index="2">
<source>BLUEPRINT.md (secciones de referencia del MVP 1: tabla de clasificación/priorización, conceptos base, HU04–HU07, HU11 y modelo de datos)</source>
<document_content>
{{PEGA_AQUI_LAS_SECCIONES_RELEVANTES_DE_BLUEPRINT.md}}
</document_content>
</document>
<document index="3">
<source>AGENTS.md (reglas de arquitectura, capas, seguridad y pruebas)</source>
<document_content>
{{PEGA_AQUI_EL_CONTENIDO_DE_AGENTS.md}}
</document_content>
</document>
</documents>

<task>
Redacta la especificación funcional y el desglose técnico de las historias de usuario necesarias para implementar el MVP 2 (ampliación de servicios de voz sobre el MVP 1), entregando en orden:
1. **Mapa inicial de historias del MVP 2** (Módulo, HU iniciando en HU16, Título, Entrega/Fase dentro del MVP 2 y Dependencia con el MVP 1).
2. **Clasificación, priorización y estimación de las historias**, usando exactamente la escala del proyecto:
   - Puntos IA (0–5) y Clasificación (Tradicional, Híbrida o Implementable principalmente con IA).
   - Prioridad MoSCoW (`Must`, `Should`, `Could`, `Won't`).
   - Esfuerzo/tiempo (`1–10`) considerando backend, frontend, integración del SDK, seguridad, accesibilidad y pruebas.
   - Justificación breve y específica por historia.
3. **Detalle completo de cada historia de usuario** necesaria para cubrir:
   - Registro de gastos e ingresos mediante voz (Speech-to-Text con `microsoft-cognitiveservices-speech-sdk`), interpretación de datos del movimiento y confirmación antes de guardar.
   - Lectura en voz alta de movimientos individuales o del historial/listado al usuario (Text-to-Speech con `microsoft-cognitiveservices-speech-sdk`), con controles de reproducción.
   - Autorización segura del servicio de voz (emisión de token temporal desde el backend sin exponer claves en el cliente) y manejo de permisos de micrófono/conectividad, ya sea como historia habilitadora o transversal.
4. **Desglose de tareas técnicas derivadas por historia**, separadas por capa/área:
   - Backend (FastAPI: dominio, aplicación, infraestructura, API, configuración y pruebas).
   - Frontend (Angular: dominio puro, servicio/adaptador del SDK, componentes standalone `OnPush` con Signals, integración con repositorios Dexie/`outbox`, accesibilidad y pruebas).
   - Contrato y calidad (`openapi.json`, regeneración con `ng-openapi-gen`, lint, tipos y build).
</task>

<instructions>
### Reglas para la clasificación, priorización y estimación
Usa exactamente estos rangos (heredados de `PROMPTS.md` y `BLUEPRINT.md`):
- **Puntos IA (qué tan viable es implementarla con apoyo de IA, no si el producto usa IA):**
  - `0–1`: Historia tradicional; requiere implementación convencional con poco beneficio de generación asistida.
  - `2–3`: Historia híbrida; la IA apoya parte del código, pero la integración con SDK externo, seguridad de tokens, manejo de audio/permisos o parsing ambiguo exige revisión humana importante.
  - `4–5`: Historia implementable principalmente con IA; patrones conocidos de UI, formateo determinista, repositorios y pruebas unitarias.
- **MoSCoW:**
  - `Must`: indispensable para que el MVP 2 cumpla su núcleo (dictar un movimiento, leer movimientos y autenticar el SDK de forma segura).
  - `Should`: mejora sustancial del uso diario (ej. lectura continua de listados, reintento o edición rápida tras dictado).
  - `Could`: mejoras de comodidad/personalización (ej. selección de velocidad de lectura o atajos adicionales).
  - `Won't`: fuera del alcance del MVP 2.
- **Esfuerzo/tiempo (1–10):** evalúa el costo real completo (configuración Azure Speech, endpoint de token, parser/formateador de texto, UI accesible, manejo de estados de error y pruebas con mocks).

### Reglas para cada historia de usuario
Cada historia debe redactarse obligatoriamente en **formato Connextra** y seguir esta estructura fija en orden:
a) Encabezado `#### HUxx. Título` (numeración consecutiva desde `HU16`).
b) Declaración en **formato Connextra** dentro de un bloque de cita:
   > **Como** [rol o perfil de usuario],
   > **quiero** [funcionalidad o acción concreta],
   > **para** [beneficio o valor esperado].
c) Contexto (1-2 frases explicando qué aporta sobre el flujo actual del MVP 1).
d) Reglas de negocio numeradas. Usa tablas cuando definas campos extraídos, comandos o formatos de lectura. Indica siempre el comportamiento con conexión y sin conexión.
e) Criterios de aceptación en Gherkin en español (`Escenario / Dado / Cuando / Entonces / Y`) con valores concretos (montos en moneda del usuario, fechas, categorías y textos exactos de interfaz o locución).
f) Casos límite (permiso de micrófono denegado, audio vacío o no entendido, monto/categoría ambigua, token expirado, pérdida de conexión durante dictado/lectura, doble clic, interrupción de reproducción).
g) Fuera de alcance, explícito.

### Decisiones del MVP 1 y MVP 2 que debes respetar sin alterarlas
- SDK obligatorio: `microsoft-cognitiveservices-speech-sdk` (Azure AI Speech) para STT y TTS en español.
- Dinero: los montos se guardan siempre como enteros en centavos (`amount_minor`), usando la moneda configurada en la cuenta del usuario (por defecto COP).
- Persistencia sin conexión: una vez confirmado el movimiento dictado por voz, se valida con las mismas reglas de HU04/HU05 y se guarda en Dexie + `outbox` en una única transacción.
- Seguridad: nunca se almacenan claves de suscripción de Azure Speech en el frontend ni en `environment.ts`; el cliente solicita un token temporal al backend usando su sesión autenticada. Los esquemas FastAPI usan `extra="forbid"`.
- Tiempo determinista: toda validación de fechas inyecta `Clock` (nunca `new Date()`, `datetime.now()` o `date.today()` en dominio).
- Conectividad: los servicios cognitivos de voz requieren internet; sin conexión, las acciones de voz informan su indisponibilidad sin bloquear el flujo manual offline del MVP 1.
</instructions>

<constraints>
- Todas las historias deben usar estrictamente el formato Connextra (`Como / quiero / para`) y responder a una necesidad observable del usuario.
- Cada regla de negocio debe ser verificable mediante una prueba automatizada y trazable a al menos una tarea técnica.
- Incluye como mínimo 4 escenarios Gherkin por historia: camino feliz, error de entrada o ambigüedad, fallo de permisos o servicio, y escenario sin conexión.
- Usa textos exactos de mensajes en pantalla y ejemplos reales de frases dictadas y leídas (nunca placeholders genéricos).
- En el desglose técnico no inventes dependencias nuevas distintas a `microsoft-cognitiveservices-speech-sdk` sin justificarlas ni preguntar primero.
- Respeta la regla de capas: el dominio no importa FastAPI, Angular, Dexie ni el SDK de voz directamente; los componentes no inyectan `HttpClient` ni `Dexie`.
- Lo que no sea imprescindible para el MVP 2 debe quedar explícitamente en "Fuera de alcance".
</constraints>

<examples>
<example>
### Ejemplo de tabla de clasificación y estimación
| HU | Historia | Puntos IA | Clasificación | MoSCoW | Esfuerzo/tiempo (1–10) | Justificación |
|---|---|---:|---|---|---:|---|
| HU16 | Emitir token temporal de voz desde el backend | 3 | Historia híbrida; combina lógica tradicional e IA | Must | 5 | Patrón HTTP estándar en FastAPI, pero exige manejo seguro de secretos de Azure Speech, caché/expiración y rate limiting. |

### Ejemplo de historia en formato Connextra y sus tareas técnicas
#### HU17. Registrar movimiento por dictado de voz

> **Como** usuario de la app de finanzas personales,
> **quiero** dictar un gasto o ingreso usando el micrófono y revisar los datos interpretados antes de guardarlo,
> **para** registrar mis movimientos en segundos sin tener que escribir manualmente en el formulario.

**Contexto:** amplía el registro rápido de HU04 y HU05 incorporando captura por voz mediante `microsoft-cognitiveservices-speech-sdk`, manteniendo las mismas validaciones de dominio y el guardado en Dexie/outbox.

**Reglas de negocio:**
1. El botón "Dictar movimiento" solo está habilitado cuando hay conexión a internet; sin conexión muestra el aviso "El registro por voz requiere conexión a internet".
2. Al activar el dictado, la app solicita permiso de micrófono si aún no fue concedido y obtiene un token temporal de voz del backend.
3. El texto transcrito se analiza para prellenar tipo (`gasto` o `ingreso`), monto, categoría coincidente y descripción; el usuario siempre debe confirmar antes de persistir.
4. Al confirmar, el movimiento se almacena como entero en centavos (`amount_minor`) en Dexie junto con su entrada en `outbox` dentro de la misma transacción.

```gherkin
Escenario: Registrar un gasto exitoso mediante dictado de voz
  Dado que tengo conexión a internet y permiso de micrófono concedido
  Cuando presiono "Dictar movimiento" y digo "Gasté veinticinco mil pesos en almuerzo en Alimentación"
  Entonces veo el formulario prellenado con tipo "Gasto", monto "$25.000", categoría "Alimentación" y descripción "Almuerzo"
  Y al presionar "Guardar movimiento" se registra en IndexedDB y se encola en el outbox para sincronizar
```

**Casos límite:** permiso de micrófono denegado, silencio prolongado o audio ininteligible, monto negativo o cero dictado, doble pulsación sobre el botón de micrófono.

**Fuera de alcance:** guardado automático sin confirmación previa, edición/eliminación por voz.

**Tareas técnicas derivadas:**
- **Frontend (Dominio):** función pura de extracción/normalización de texto transcrito a borrador de movimiento (`type`, `amount_minor`, `category_id`, `description`, `date` vía `Clock`) + pruebas unitarias en Vitest.
- **Frontend (Infraestructura/SDK):** servicio adaptador que encapsula `SpeechConfig` y `SpeechRecognizer` de `microsoft-cognitiveservices-speech-sdk` usando token temporal + pruebas con mock del SDK.
- **Frontend (UI):** botón/estado de grabación en el formulario de movimientos (`OnPush`, Signals, `@if`, `aria-live="polite"`) que prellena el formulario reactivo tipado sin romper el flujo manual.
</example>
</examples>

<stop_conditions>
Antes de redactar, si detectas una contradicción con `BLUEPRINT.md`, `AGENTS.md` o `docs/MVP2.md`, o si falta una definición imprescindible (por ejemplo, si el usuario podrá confirmar el movimiento por voz o solo en pantalla, o el idioma/locale objetivo como `es-CO`), detente, enumera las preguntas concretas y espera respuesta. No asumas decisiones no documentadas.
</stop_conditions>

<output_format>
Entrega un único documento Markdown estructurado en:
1. Mapa de historias del MVP 2.
2. Tabla de clasificación (Puntos IA), priorización (MoSCoW), estimación de esfuerzo (1–10) y justificación.
3. Detalle completo de cada historia (`HU16` en adelante) en formato Connextra, con reglas, bloques ```gherkin, casos límite, fuera de alcance y tareas técnicas derivadas por capa.
4. Resumen consolidado de tareas técnicas (Backend, Frontend y Calidad/Contrato).
Sin texto introductorio ni despedida.
</output_format>

<verification>
Antes de entregar, razona dentro de `<thinking>` (sin incluir ese razonamiento en la respuesta final) y verifica:
- [ ] Todas las historias usan el formato Connextra (`Como / quiero / para`) en bloque de cita.
- [ ] Todas las historias aparecen en la tabla con Puntos IA (0–5), Clasificación, MoSCoW, Esfuerzo (1–10) y Justificación coherente.
- [ ] Las historias cubren STT (registro), TTS (lectura) y autorización segura con `microsoft-cognitiveservices-speech-sdk`.
- [ ] Cada historia incluye al menos 4 escenarios Gherkin concretos y comportamiento explícito sin conexión.
- [ ] Cada tarea técnica respeta la arquitectura hexagonal, `amount_minor`, `Clock`, Dexie + `outbox` y no exposición de secretos.
</verification>

¿Qué tareas técnicas salen a partir de este prompt?

Al ejecutar ese prompt sobre tu arquitectura actual (AGENTS.md y DOCUMENTACIONMVP.md), las tareas técnicas se agrupan naturalmente en cuatro bloques:

Backend (FastAPI) — Autorización segura del SDK:

Configuración de variables de entorno en Settings (clave/región de Azure Speech, nunca en el repositorio ni en el frontend).
Nuevo módulo o endpoint protegido por JWT (p. ej. obtención de token temporal de Azure AI Speech con límite de peticiones en Redis y esquemas extra="forbid").
Pruebas unitarias y de integración (pytest con cliente HTTP simulado para Azure) y exportación actualizada de openapi.json.

Frontend (Angular) — Capa de voz e integración con microsoft-cognitiveservices-speech-sdk:

Instalación de microsoft-cognitiveservices-speech-sdk (previa autorización según regla de dependencias) y regeneración del cliente API con ng-openapi-gen.
Adaptador/servicio de voz desacoplado (SpeechConfig, SpeechRecognizer para STT y SpeechSynthesizer para TTS) con gestión de ciclo de vida, cancelación, permisos de micrófono y renovación del token temporal.
Lógica pura de dominio:
Parser de dictado a borrador de movimiento (type, amount_minor en centavos, coincidencia de categoría por name_key, fecha con Clock).
Formateador de movimientos a texto natural en español para lectura TTS (monto en moneda del usuario, categoría, fecha y descripción).

Frontend (Angular) — UI y persistencia offline-first:

Controles de dictado en el flujo de creación de movimientos (prellenado de formulario reactivo tipado y confirmación manual que persiste en Dexie + outbox en la misma transacción).
Controles de reproducción/detención de lectura en voz alta en el detalle o historial de movimientos.
Manejo de estados sin conexión (deshabilitar/avisar indisponibilidad de voz sin afectar el flujo offline del MVP 1) y accesibilidad (aria-live, etiquetas y navegación por teclado).

Calidad y pruebas:

Pruebas unitarias de parser/formateador (sin DOM ni SDK real) y pruebas de servicios/componentes en Vitest con mocks de microsoft-cognitiveservices-speech-sdk.
Verificación completa de puertas de salida: ruff, mypy, pytest en backend; lint, test:ci y build en frontend.


---

## 4. Historias de usuario del MVP 2 y desglose técnico

### 4.1. Mapa de historias del MVP 2

| Módulo | HU | Historia | Fase MVP 2 | Dependencia con MVP 1 |
|---|---|---|---|---|
| 6. Servicios de voz | HU16 | Autorización segura y disponibilidad del servicio de voz | MVP2-R1 (Núcleo) | HU02 (Sesión JWT), FastAPI y Redis |
| 6. Servicios de voz | HU17 | Registrar movimiento mediante dictado de voz | MVP2-R1 (Núcleo) | HU04, HU05, HU08, HU14, HU16, Dexie/`outbox` |
| 6. Servicios de voz | HU18 | Escuchar detalle de un movimiento en voz alta | MVP2-R1 (Núcleo) | HU11, HU16 |
| 6. Servicios de voz | HU19 | Escuchar listado de movimientos del historial en voz alta | MVP2-R2 (Mejora) | HU11, HU16, HU18 |

---

### 4.2. Clasificación, priorización y estimación

| HU | Historia | Puntos IA | Clasificación | MoSCoW | Esfuerzo/tiempo (1–10) | Justificación |
|---|---|---:|---|---|---:|---|
| HU16 | Autorización segura y disponibilidad del servicio de voz | 3 | Historia híbrida; combina lógica tradicional e IA | Must | 5 | Sigue el patrón HTTP de FastAPI y Redis del MVP 1, pero requiere manejo estricto de secretos de Azure AI Speech, emisión/renovación de token temporal y rate limiting. |
| HU17 | Registrar movimiento mediante dictado de voz | 2 | Historia híbrida; combina lógica tradicional e IA | Must | 8 | Integra `SpeechRecognizer` de `microsoft-cognitiveservices-speech-sdk`, permisos de micrófono, parser determinista en español a `amount_minor`/categorías y guardado atómico en Dexie/`outbox`. |
| HU18 | Escuchar detalle de un movimiento en voz alta | 4 | Historia implementable principalmente con IA | Must | 5 | Formateo determinista de un movimiento a texto natural en español y reproducción mediante `SpeechSynthesizer` con controles accesibles y pruebas simuladas. |
| HU19 | Escuchar listado de movimientos del historial en voz alta | 4 | Historia implementable principalmente con IA | Should | 6 | Reutiliza la síntesis de HU18 con cola secuencial sobre los registros locales de HU11, controles de pausa/siguiente/detener y seguimiento visual del elemento activo. |

---

### 4.3. Detalle de historias de usuario (formato Connextra)

#### HU16. Autorización segura y disponibilidad del servicio de voz

> **Como** usuario autenticado de la app de finanzas personales,
> **quiero** que la aplicación gestione automáticamente una autorización temporal y segura para los servicios de voz cuando tenga conexión,
> **para** usar el dictado y la lectura de movimientos sin exponer credenciales en el navegador ni configurar claves manualmente.

**Contexto:** habilita el uso seguro de `microsoft-cognitiveservices-speech-sdk` desde la PWA Angular reutilizando la sesión JWT del MVP 1, de modo que la clave de suscripción de Azure AI Speech permanezca exclusivamente en el backend.

**Reglas de negocio:**
1. **Emisión de token temporal (`POST /speech/token`):** el backend expone un endpoint protegido por JWT que solicita un token temporal a Azure AI Speech y devuelve únicamente `token`, `region` y `expires_in_seconds` (vigencia máxima de 600 segundos). El cuerpo de entrada no acepta parámetros adicionales (`extra="forbid"`).
2. **Protección de secretos y logs:** la clave `AZURE_SPEECH_KEY` nunca se envía al cliente, no existe en `environment.ts` ni en `environment.development.ts`, y nunca se registra junto con el `token` en logs del servidor ni del navegador.
3. **Límite de solicitudes:** el backend limita las solicitudes de token mediante Redis a un máximo de **30 por hora por `user_id`** (tomado exclusivamente del JWT). Si se excede, responde HTTP `429` y el cliente muestra `"Has alcanzado el límite temporal del servicio de voz. Intenta más tarde"`.
4. **Indisponibilidad en servidor:** si `AZURE_SPEECH_KEY` o `AZURE_SPEECH_REGION` no están configuradas o Azure AI Speech falla, el backend responde HTTP `503` con código `SPEECH_SERVICE_UNAVAILABLE` y el cliente muestra `"El servicio de voz no está disponible en este momento"`.
5. **Caché en memoria en frontend:** el cliente conserva el token temporal únicamente en memoria (nunca en `localStorage` ni en IndexedDB) y lo renueva automáticamente cuando resten menos de 60 segundos para su expiración.
6. **Comportamiento con conexión y sin conexión:**
   - **Con conexión:** solicita o reutiliza el token temporal al iniciar cualquier operación de voz.
   - **Sin conexión:** antes de llamar a la API, el cliente detecta la ausencia de red, evita llamadas fallidas y muestra `"Los servicios de voz requieren conexión a internet"`, manteniendo plenamente operativas las funciones manuales offline del MVP 1.

**Criterios de aceptación:**

```gherkin
Escenario: Obtención exitosa de token temporal de voz
  Dado que tengo la sesión iniciada y conexión a internet
  Cuando inicio por primera vez una acción de voz
  Entonces la aplicación envía una petición autenticada a POST /speech/token
  Y recibe un token temporal con región "eastus" y vigencia de 600 segundos sin recibir la clave de suscripción

Escenario: Límite de solicitudes excedido al pedir tokens de voz
  Dado que mi usuario ya realizó 30 solicitudes a POST /speech/token en la última hora
  Cuando intento iniciar una nueva operación que requiere renovar el token de voz
  Entonces el servidor responde con estado 429
  Y veo el mensaje "Has alcanzado el límite temporal del servicio de voz. Intenta más tarde"

Escenario: Servicio de voz no configurado o caído en el servidor
  Dado que el backend no tiene configuradas las credenciales de Azure AI Speech o el proveedor no responde
  Cuando la aplicación solicita autorización a POST /speech/token
  Entonces el servidor responde con estado 503 y código "SPEECH_SERVICE_UNAVAILABLE"
  Y veo el mensaje "El servicio de voz no está disponible en este momento"

Escenario: Verificación de disponibilidad sin conexión a internet
  Dado que el dispositivo se encuentra sin conexión
  Cuando intento activar una función de voz
  Entonces la aplicación no realiza peticiones a POST /speech/token
  Y veo el mensaje "Los servicios de voz requieren conexión a internet"
  Y puedo seguir registrando y consultando movimientos manualmente sin conexión
```

**Casos límite:**
- Token temporal vencido tras inactividad de la pestaña: se solicita uno nuevo automáticamente antes de invocar el SDK.
- Access token JWT vencido (`401`): el interceptor del MVP 1 renueva la sesión mediante `/auth/refresh` y reintenta `POST /speech/token`.
- Solicitudes concurrentes desde varios componentes: se reutiliza la misma petición en vuelo para no consumir cuota adicional.
- Tiempo de espera agotado al contactar Azure desde el backend: responde HTTP `503` sin afectar otros endpoints.

**Fuera de alcance:** configuración manual de región/clave por el usuario en ajustes, soporte de voz sin conexión mediante modelos locales, métricas históricas de minutos de uso por cuenta.

**Tareas técnicas derivadas:**
- **Backend (Configuración y Dominio):**
  - Agregar `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` y `AZURE_SPEECH_TOKEN_TIMEOUT_SECONDS` en `backend/app/config.py` y documentarlas sin secretos en `backend/.env.example`.
  - Crear `backend/app/modules/speech/domain/` con errores de dominio (`SpeechUnavailableError`, `SpeechRateLimitError`) y modelo `SpeechToken`.
- **Backend (Aplicación, Infraestructura y API):**
  - Definir puerto `SpeechTokenProvider` (`Protocol`) y caso de uso `IssueSpeechToken` (con `RateLimiter` de Redis y `Clock`) en `backend/app/modules/speech/application/`.
  - Implementar adaptador HTTP en `backend/app/modules/speech/infrastructure/` para solicitar el token a `https://<region>.api.cognitive.microsoft.com/sts/v1.0/issueToken`.
  - Exponer `POST /speech/token` en `backend/app/modules/speech/api/router.py` con esquema de entrada `extra="forbid"`, registrado en `main.py` y ensamblado en `composition.py`.
- **Frontend (Core):**
  - Exportar `backend/openapi.json` y regenerar el cliente con `ng-openapi-gen`.
  - Implementar `SpeechAuthService` en `frontend/src/app/core/` usando signals en memoria, coalescencia de llamadas y chequeo previo de conectividad.
- **Pruebas:**
  - `pytest`: unitarias de `IssueSpeechToken` (fakes) e integración de `POST /speech/token` (mock HTTP de Azure + Redis real).
  - `Vitest`: unitarias de `SpeechAuthService` (caché, expiración, `429`, `503`, offline).

---

#### HU17. Registrar movimiento mediante dictado de voz

> **Como** usuario de la app de finanzas personales,
> **quiero** dictar un gasto o ingreso usando el micrófono y revisar los datos interpretados antes de guardarlo,
> **para** registrar mis movimientos en segundos sin tener que escribir manualmente en el formulario.

**Contexto:** amplía el registro rápido de gastos (HU04) e ingresos (HU05) incorporando captura por voz mediante `SpeechRecognizer` de `microsoft-cognitiveservices-speech-sdk`, manteniendo intactas las validaciones de dominio y la persistencia offline-first en Dexie + `outbox`.

**Reglas de negocio:**
1. **Acceso en pantalla:** el formulario de creación de movimiento ("+" de HU04/HU05) incluye el botón `"Dictar movimiento"` con indicadores accesibles de estado (`Listo`, `Escuchando...`, `Procesando...`).
2. **Configuración del SDK:** utiliza `SpeechConfig.fromAuthorizationToken(token, region)`, `AudioConfig.fromDefaultMicrophoneInput()` y `SpeechRecognizer` de `microsoft-cognitiveservices-speech-sdk` configurado para reconocimiento en español (`es-CO` por defecto).
3. **Permisos de micrófono:** al presionar `"Dictar movimiento"` con conexión, solicita permiso de micrófono si no fue otorgado. Si el navegador lo deniega, muestra `"Permiso de micrófono denegado. Habilítalo en tu navegador o registra manualmente"`.
4. **Reglas de interpretación determinista del dictado:** el dominio convierte la transcripción en un borrador de movimiento así:

   | Campo | Regla de extracción | Si no se detecta en el dictado |
   |---|---|---|
   | **Tipo** (`type`) | Verbos/palabras clave de ingreso (`"ingreso"`, `"ingresé"`, `"recibí"`, `"me pagaron"`, `"salario"`, `"cobré"`) → `income`; de gasto (`"gasté"`, `"pagué"`, `"compré"`, `"gasto"`) → `expense`. | `expense` (predeterminado en HU05) |
   | **Monto** (`amount_minor`) | Parsea cifras numéricas (`"25000"`, `"25.000"`, `"1250000,50"`) o montos hablados en español (`"veinticinco mil pesos"`) a entero en centavos (`amount_minor`), validando > 0 y hasta 13 dígitos. | Vacío y foco/resaltado con `"No pudimos detectar el monto. Ingrésalo para continuar"` |
   | **Categoría** (`category_id`) | Compara mediante `name_key` (minúsculas y sin tildes, según HU08) contra las categorías activas del usuario del tipo correspondiente. | Última categoría usada de ese tipo o `"Otros gastos"` / `"Otros ingresos"` |
   | **Fecha** (`occurred_on`) | Reconoce `"hoy"` o `"ayer"` respecto al `Clock` inyectado. Si detecta una referencia futura explícita, muestra `"La fecha no puede ser futura"`. | Fecha de hoy (vía `Clock`) |
   | **Descripción** (`description`) | Extrae el concepto restante limpio de palabras de comando y categoría, truncado o validado a máximo 100 caracteres. | Vacío (opcional según HU04) |

5. **Confirmación obligatoria antes de guardar:** el sistema nunca persiste automáticamente tras escuchar; siempre prellena el formulario reactivo para que el usuario revise o ajuste los valores y pulse `"Guardar"`.
6. **Guardado y alertas:** al pulsar `"Guardar"`, se aplican exactamente las validaciones de HU04/HU05 y alertas de presupuesto de HU14, guardando el movimiento en Dexie y su evento en `outbox` dentro de la misma transacción, con el mensaje `"Gasto guardado"` o `"Ingreso guardado"`.
7. **Comportamiento con conexión y sin conexión:**
   - **Con conexión:** habilita el dictado por micrófono vía `microsoft-cognitiveservices-speech-sdk`.
   - **Sin conexión:** deshabilita o bloquea el inicio del dictado mostrando `"El registro por voz requiere conexión a internet"`, mientras el registro manual de HU04/HU05 sigue funcionando normalmente sin conexión.

**Criterios de aceptación:**

```gherkin
Escenario: Dictar un gasto completo y guardarlo tras confirmar
  Dado que tengo conexión a internet, sesión activa y permiso de micrófono concedido
  Y tengo activa la categoría de gasto "Alimentación"
  Cuando abro el formulario de movimiento, presiono "Dictar movimiento" y digo "Gasté veinticinco mil pesos en almuerzo en Alimentación"
  Entonces veo el formulario prellenado con tipo "Gasto", monto "$25.000", categoría "Alimentación", fecha de hoy y descripción "Almuerzo"
  Y cuando presiono "Guardar"
  Entonces el gasto se guarda en Dexie con amount_minor 2500000 y se encola en el outbox en la misma transacción
  Y veo el mensaje "Gasto guardado"

Escenario: Dictar un ingreso válido
  Dado que tengo conexión a internet y permiso de micrófono concedido
  Y tengo activa la categoría de ingreso "Salario"
  Cuando presiono "Dictar movimiento" y digo "Recibí tres millones quinientos mil pesos de Salario"
  Entonces veo el formulario prellenado con tipo "Ingreso", monto "$3.500.000" y fuente "Salario"
  Y al presionar "Guardar" veo "Ingreso guardado" y los ingresos del mes aumentan en $3.500.000

Escenario: Dictado ambiguo sin monto reconocible
  Dado que tengo conexión a internet y permiso de micrófono concedido
  Cuando presiono "Dictar movimiento" y digo "Pagué un café en Ocio"
  Entonces veo el formulario prellenado con tipo "Gasto", categoría "Ocio" y descripción "Café"
  Y el campo monto aparece vacío con el mensaje "No pudimos detectar el monto. Ingrésalo para continuar"
  Y el botón "Guardar" permanece deshabilitado hasta ingresar un monto mayor que 0

Escenario: Permiso de micrófono denegado
  Dado que tengo conexión a internet
  Cuando presiono "Dictar movimiento" y deniego el permiso de micrófono en el navegador
  Entonces el reconocimiento de voz no se inicia
  Y veo el mensaje "Permiso de micrófono denegado. Habilítalo en tu navegador o registra manualmente"

Escenario: Intento de dictado sin conexión a internet
  Dado que el dispositivo se encuentra sin conexión
  Cuando abro el formulario de nuevo movimiento e intento usar "Dictar movimiento"
  Entonces veo el mensaje "El registro por voz requiere conexión a internet"
  Y puedo ingresar manualmente "$18.000" en "Transporte" y guardar el gasto sin conexión
```

**Casos límite:**
- Silencio prolongado o audio no reconocido (`ResultReason.NoMatch`): finaliza la escucha y muestra `"No se reconoció ningún movimiento. Intenta de nuevo o escribe los datos"`.
- Monto cero o negativo dictado: deja el campo inválido con `"Ingresa un monto mayor que 0"` (HU04).
- Pérdida de conexión durante la captura: cancela la sesión del `SpeechRecognizer`, libera el micrófono, conserva lo que ya esté en el formulario y muestra `"Se perdió la conexión durante el dictado. Puedes completar el registro manualmente"`.
- Doble clic sobre `"Dictar movimiento"` mientras escucha: no abre dos reconocedores simultáneos; el segundo toque detiene o ignora según estado activo.

**Fuera de alcance:** guardado automático sin confirmación visual del usuario, comandos de voz para editar o eliminar movimientos (HU06/HU07), dictado de reglas recurrentes (HU09) o etiquetas `#tag` (HU10), activación continua por palabra clave (*wake-word*).

**Tareas técnicas derivadas:**
- **Frontend (Dominio):**
  - Crear parser puro `parseVoiceTransactionDraft(transcript, categories, clock, lastUsedByType)` en `frontend/src/app/features/movimientos/domain/` para convertir texto y números en español a `amount_minor`, `type`, `category_id`, `occurred_on` y `description`.
- **Frontend (Infraestructura / SDK):**
  - Crear puerto/servicio `SpeechRecognitionService` que encapsula `SpeechConfig`, `AudioConfig` y `SpeechRecognizer` de `microsoft-cognitiveservices-speech-sdk`, obtiene token desde `SpeechAuthService` y libera recursos al cancelar o destruir el componente.
- **Frontend (UI y Repositorio):**
  - Integrar botón `"Dictar movimiento"`, indicador de escucha y región `aria-live="polite"` en el formulario de movimiento (`OnPush`, Signals, `@if`, formulario reactivo tipado), manteniendo el guardado a través del repositorio existente (Dexie + `outbox`).
- **Pruebas:**
  - `Vitest` (unitarias de dominio): parsing de cifras y palabras en español, `amount_minor`, coincidencia por `name_key`, fechas `"hoy"`/`"ayer"`/`futura` con `Clock` falso.
  - `Vitest` (componente/servicio): mock de `SpeechRecognizer`, permiso denegado, `NoMatch`, pérdida de red y guardado offline manual.

---

#### HU18. Escuchar detalle de un movimiento en voz alta

> **Como** usuario de la app de finanzas personales,
> **quiero** escuchar en voz alta los datos de un movimiento registrado desde su vista de detalle o fila del historial,
> **para** verificar su monto, categoría, fecha y descripción sin tener que leer la pantalla.

**Contexto:** incorpora capacidades Text-to-Speech mediante `SpeechSynthesizer` de `microsoft-cognitiveservices-speech-sdk` sobre los movimientos ya almacenados localmente (HU11), mejorando la accesibilidad y la revisión rápida.

**Reglas de negocio:**
1. **Control de reproducción:** en el detalle del movimiento (y accesible desde su fila en el historial) existe el botón `"Escuchar movimiento"`. Mientras reproduce, cambia a `"Detener lectura"` para interrumpir el audio en cualquier momento.
2. **Formato de locución en español:** el dominio construye un texto claro y natural a partir del movimiento almacenado en Dexie:

   | Elemento | Regla de locución | Ejemplo |
   |---|---|---|
   | **Tipo y monto** | `"Gasto de <monto formateado>"` o `"Ingreso de <monto formateado>"` usando la moneda del usuario. | `"Gasto de veinticinco mil pesos"` / `"Gasto de $25.000"` |
   | **Categoría** | `"en la categoría <nombre de categoría>"` (o `"fuente <nombre>"` para ingreso). | `"en la categoría Alimentación"` |
   | **Fecha** | Relativa si corresponde a hoy o ayer según `Clock`; si no, fecha legible. | `"registrado hoy"` / `"registrado el 12 de octubre"` |
   | **Descripción / Nota** | Se incluye si existe; si la descripción está vacía, se omite sin leer campos en blanco. | `"concepto: Almuerzo"` |

3. **Síntesis con el SDK:** utiliza `SpeechConfig.fromAuthorizationToken` y `SpeechSynthesizer` de `microsoft-cognitiveservices-speech-sdk` con voz neuronal en español (por defecto `es-CO-SalomeNeural` o voz configurable del paquete español del SDK).
4. **Exclusividad de audio:** iniciar la lectura de un movimiento detiene automáticamente cualquier otra reproducción de voz en curso.
5. **Comportamiento con conexión y sin conexión:**
   - **Con conexión:** obtiene el token temporal (HU16), sintetiza el audio con `microsoft-cognitiveservices-speech-sdk` y lo reproduce.
   - **Sin conexión:** no intenta llamar al SDK ni falla silenciosamente; muestra `"La lectura por voz requiere conexión a internet"`, manteniendo visible todo el detalle del movimiento desde Dexie.

**Criterios de aceptación:**

```gherkin
Escenario: Escuchar el detalle de un gasto con todos sus datos
  Dado que tengo conexión a internet y existe un gasto de $25.000 en "Alimentación" con descripción "Almuerzo" de fecha hoy
  Cuando presiono "Escuchar movimiento"
  Entonces la aplicación obtiene autorización válida y llama al sintetizador de voz en español
  Y reproduce el enunciado "Gasto de $25.000 en la categoría Alimentación, registrado hoy, concepto: Almuerzo"
  Y mientras dura la reproducción el botón muestra "Detener lectura"

Escenario: Detener la lectura en curso
  Dado que la aplicación está leyendo en voz alta un ingreso de $3.500.000 en "Salario"
  Cuando presiono "Detener lectura"
  Entonces el audio se detiene de inmediato
  Y el botón vuelve al estado "Escuchar movimiento"

Escenario: Fallo del servicio de síntesis de voz
  Dado que tengo conexión a internet
  Cuando presiono "Escuchar movimiento" y el servicio de Azure AI Speech devuelve un error de síntesis
  Entonces el botón vuelve al estado "Escuchar movimiento"
  Y veo el mensaje "No se pudo reproducir el movimiento. Intenta nuevamente"

Escenario: Intento de lectura sin conexión a internet
  Dado que el dispositivo se encuentra sin conexión
  Cuando abro el detalle de un movimiento y presiono "Escuchar movimiento"
  Entonces no se realiza petición al servicio de voz
  Y veo el mensaje "La lectura por voz requiere conexión a internet"
  Y el detalle del movimiento sigue visible en pantalla desde IndexedDB
```

**Casos límite:**
- Movimiento sin descripción ni nota: omite `"concepto:"` y lee únicamente tipo, monto, categoría y fecha.
- Salir de la pantalla o cerrar el modal durante la reproducción: el ciclo de vida de Angular (`DestroyRef`) detiene y cierra el `SpeechSynthesizer` inmediatamente.
- Doble clic rápido sobre `"Escuchar movimiento"`: ignora clics repetidos mientras se prepara el audio o alterna limpiamente a detener.
- Movimiento marcado como pendiente de sincronizar (`⏳`): se lee normalmente con los datos locales de Dexie sin mencionar detalles técnicos internos.

**Fuera de alcance:** descarga del audio en MP3, selección de múltiples voces o velocidades por el usuario, lectura de gráficos ECharts (HU15) o presupuestos (HU14).

**Tareas técnicas derivadas:**
- **Frontend (Dominio):**
  - Crear función pura `formatTransactionForSpeech(transaction, category, currency, clock)` en `frontend/src/app/features/movimientos/domain/` que genere el texto legible en español sin importar Angular ni el SDK.
- **Frontend (Infraestructura / SDK):**
  - Crear servicio `SpeechSynthesisService` en `frontend/src/app/core/` que encapsula `SpeechSynthesizer` de `microsoft-cognitiveservices-speech-sdk`, garantizando reproducción única simultánea y limpieza de audio.
- **Frontend (UI):**
  - Añadir botón accesible `"Escuchar movimiento"` / `"Detener lectura"` con estado reactivo (`signal`) y anuncio `aria-live="polite"` en el componente de detalle de movimiento (`OnPush`, `@if`).
- **Pruebas:**
  - `Vitest` (unitarias): formateo de gastos/ingresos con y sin descripción, moneda COP, fechas `"hoy"`/`"ayer"`/pasadas vía `Clock`.
  - `Vitest` (integración): mock de `SpeechSynthesizer`, reproducción, detención manual, limpieza al destruir componente, error de síntesis y modo offline.

---

#### HU19. Escuchar listado de movimientos del historial en voz alta

> **Como** usuario que consulta su historial financiero,
> **quiero** reproducir en voz alta un resumen secuencial de los movimientos visibles en el historial con controles para pausar, avanzar o detener,
> **para** repasar mi actividad del día o de una búsqueda sin tener que leer cada fila en la pantalla.

**Contexto:** extiende HU18 sobre la pantalla de historial de movimientos (HU11) y resultados locales (HU12), permitiendo la lectura continua de los movimientos cargados desde Dexie mediante `SpeechSynthesizer`.

**Reglas de negocio:**
1. **Alcance de la lectura:** en la vista de historial (HU11), el botón `"Escuchar historial"` lee en orden los movimientos actualmente visibles/filtrados en pantalla (respetando el orden descendente de HU11), anunciando primero la cantidad a leer (por ejemplo: `"Leyendo 3 movimientos"`).
2. **Límite por sesión de lectura:** para evitar locuciones interminables en historiales largos (como los 2.000 registros contemplados en HU11), lee en bloques de hasta **10 movimientos por reproducción**; al finalizar el bloque, informa `"Fin de los primeros 10 movimientos"` y permite continuar con los siguientes si existen más cargados.
3. **Controles de reproducción:** mientras está activa la lectura del listado, se muestra una barra compacta accesible con controles `"Pausar"` / `"Reanudar"`, `"Siguiente"` y `"Detener"`, además de resaltar visualmente la fila del movimiento que se está leyendo en ese instante.
4. **Historial vacío:** si no hay movimientos visibles en pantalla, el botón `"Escuchar historial"` no aparece o informa `"No hay movimientos para leer"`.
5. **Comportamiento con conexión y sin conexión:**
   - **Con conexión:** lee los datos obtenidos localmente desde Dexie sintetizando cada elemento mediante `microsoft-cognitiveservices-speech-sdk` (token de HU16).
   - **Sin conexión:** muestra `"La lectura por voz requiere conexión a internet"`, manteniendo disponible el historial completo en pantalla desde Dexie.

**Criterios de aceptación:**

```gherkin
Escenario: Reproducir en voz alta los movimientos visibles del historial
  Dado que tengo conexión a internet y 3 movimientos visibles en el historial de hoy
  Cuando presiono "Escuchar historial"
  Entonces veo la barra de control con "Pausar", "Siguiente" y "Detener"
  Y escucho "Leyendo 3 movimientos" seguido de la lectura secuencial de los 3 movimientos
  Y cada fila se resalta en pantalla mientras está siendo leída

Escenario: Saltar al siguiente movimiento y detener la lectura
  Dado que se está leyendo el primer movimiento de una lista de 3
  Cuando presiono "Siguiente"
  Entonces se interrumpe el audio actual y comienza inmediatamente la lectura del segundo movimiento
  Y cuando presiono "Detener" la barra de reproducción se oculta y la fila deja de estar resaltada

Escenario: Historial sin movimientos disponibles para leer
  Dado que estoy en la pantalla "Movimientos" sin registros
  Cuando consulto las acciones disponibles o intento escuchar el historial
  Entonces veo "No hay movimientos para leer" y no se llama al servicio de síntesis de voz

Escenario: Pérdida de conexión durante la lectura secuencial
  Dado que se está leyendo el segundo movimiento de una lista
  Cuando se pierde la conexión a internet antes de sintetizar el tercer movimiento
  Entonces la reproducción se detiene de forma controlada
  Y veo el mensaje "La lectura por voz requiere conexión a internet"
  Y el historial en pantalla permanece accesible desde IndexedDB
```

**Casos límite:**
- Cambio de filtros o navegación a otra ruta mientras se reproduce la lista: detiene la cola de lectura y limpia recursos del SDK automáticamente.
- Movimiento eliminado desde otra acción mientras la cola avanza: omite elementos con `deleted_at` y continúa con el siguiente válido.
- Renovación de token durante lectura de lista larga: si el token se acerca a expirar entre un movimiento y el siguiente, `SpeechAuthService` lo renueva transparentemente antes de continuar.

**Fuera de alcance:** lectura automática al abrir la app sin acción del usuario, comandos de voz tipo `"siguiente"` mientras habla la app (barge-in por micrófono), lectura completa de los 2.000 registros sin paginación de bloques.

**Tareas técnicas derivadas:**
- **Frontend (Dominio / Estado de cola):**
  - Crear helper puro `buildHistorySpeechQueue(transactions, categories, maxItems = 10)` para construir la secuencia de textos de locución sin dependencias externas.
- **Frontend (Servicio y UI):**
  - Ampliar `SpeechSynthesisService` con cola cancelable (`playQueue`, `pause`, `resume`, `next`, `stop`) exponiendo el `transactionId` activo mediante `signal`.
  - Crear componente standalone `VoicePlayerBarComponent` (`OnPush`, Signals, `@if`, controles accesibles con `aria-label`) e integrarlo en la página de historial (`HU11`) respetando lectura exclusiva desde el repositorio local.
- **Pruebas:**
  - `Vitest`: pruebas unitarias de `buildHistorySpeechQueue` (límite de 10 ítems, lista vacía, exclusión de borrados lógicos) y pruebas de componente/cola (`next`, `pause`/`resume`, `stop`, corte de red y destrucción de vista).

---

### 4.4. Resumen consolidado de tareas técnicas del MVP 2

| Área | Archivo / Módulo objetivo | Responsabilidad principal | Historias |
|---|---|---|---|
| **Backend — Config y Composición** | `backend/app/config.py`, `main.py`, `composition.py`, `.env.example` | Declarar configuración opcional de Azure Speech y registrar el módulo `speech` sin exponer secretos. | HU16 |
| **Backend — Módulo `speech`** | `backend/app/modules/speech/{domain,application,infrastructure,api}` | Puerto `SpeechTokenProvider`, caso de uso `IssueSpeechToken`, límite en Redis (30/h), adaptador HTTP Azure STS y endpoint `POST /speech/token` (`extra="forbid"`). | HU16 |
| **Backend — Pruebas y OpenAPI** | `backend/tests/{unit,integration}/`, `backend/openapi.json` | Pruebas con `pytest` (`ruff`, `mypy`, `pytest` en verde) y exportación del esquema OpenAPI actualizado. | HU16 |
| **Frontend — Contrato API** | Cliente generado con `ng-openapi-gen` | Generar tipos y servicio cliente para `POST /speech/token`. | HU16 |
| **Frontend — Core de Voz** | `frontend/src/app/core/speech/` (`SpeechAuthService`, `SpeechRecognitionService`, `SpeechSynthesisService`) | Gestión en memoria del token temporal, encapsulamiento de `microsoft-cognitiveservices-speech-sdk` (`SpeechRecognizer` y `SpeechSynthesizer`), permisos y estado de red. | HU16, HU17, HU18, HU19 |
| **Frontend — Dominio Movimientos** | `frontend/src/app/features/movimientos/domain/` | Parser determinista de dictado a borrador (`amount_minor`, `name_key`, `Clock`) y formateador/cola de locución en español. | HU17, HU18, HU19 |
| **Frontend — UI y Repositorios** | `frontend/src/app/features/movimientos/{pages,components}/` | Botón `"Dictar movimiento"`, prellenado de formulario con confirmación hacia Dexie/`outbox`, botón `"Escuchar movimiento"` y barra `VoicePlayerBarComponent` (`OnPush`, Signals, `@if`, `aria-live`). | HU17, HU18, HU19 |
| **Frontend — Calidad y Pruebas** | `*.spec.ts` (Vitest) | Pruebas unitarias de dominio y pruebas de servicios/componentes con mocks del SDK (`npm run lint`, `npm run test:ci`, `npm run build`). | HU16–HU19 |

---

## 5. Prompts de implementación por historia (BackFinanzas)

> **Uso:** cada prompt es autocontenido y se entrega a un agente de código (Claude Code, Codex, etc.) abierto en la raíz del repositorio **BackFinanzas** (rama `dev`). Implementa una historia por sesión y en orden: **HU16 → HU17 → HU18 → HU19** (HU17–HU19 dependen del contrato de HU16).
>
> **Alcance del repositorio:** BackFinanzas solo contiene el backend (FastAPI). Las tareas de Angular/Dexie/SDK descritas en la sección 4.3 viven en el repositorio **FrontFinanzas** y quedan fuera de estos prompts; aquí se implementa y verifica el **lado servidor** de cada historia (contrato, seguridad, sincronización y pruebas de regresión).

### 5.1. Prompt HU16 — Autorización segura y disponibilidad del servicio de voz

```xml
<role>
Eres un ingeniero backend senior experto en Python 3.12, FastAPI, Pydantic v2, Redis y arquitectura hexagonal (monolito modular). Escribes código tipado (`mypy --strict`), probado con pytest y seguro por defecto. Sigues al pie de la letra las reglas de `AGENTS.md`.
</role>

<context>
Repositorio: BackFinanzas (rama `dev`). Backend FastAPI + PostgreSQL + Redis organizado en `backend/app/modules/<módulo>/{api,application,domain,infrastructure}` (módulos existentes: auth, categories, transactions, recurring, budgets, sync).
El MVP 2 añade servicios de voz con `microsoft-cognitiveservices-speech-sdk` en el frontend. Para no exponer la clave de Azure AI Speech en el navegador, el backend debe emitir un token temporal a usuarios autenticados. Esta historia es habilitadora: HU17, HU18 y HU19 dependen de ella.

Piezas existentes que DEBES reutilizar (no reimplementar):
- `app/shared/clock.py` → `Clock` (Protocol) y `SystemClock`.
- `app/modules/auth/application/ports.py` → `RateLimiter` (Protocol) y `app/modules/auth/infrastructure/rate_limiter.py` → `RedisRateLimiter.incr(key, window_seconds)`.
- `app/modules/auth/api/deps.py` → dependencia que resuelve el usuario autenticado desde el JWT.
- `app/config.py` → `Settings` (pydantic-settings), `app/composition.py` (ensamblado de casos de uso) y `app/main.py` (registro de routers).
</context>

<documents>
- `docs/MVP2.md` → sección `#### HU16. Autorización segura y disponibilidad del servicio de voz` (reglas 1–6, criterios Gherkin, casos límite, tareas técnicas). Léela completa antes de empezar.
- `AGENTS.md` → reglas que no se rompen, convenciones y formato de reporte.
- `BLUEPRINT.md` → solo la sección `#### HU02` (sesión JWT) y el apartado de errores de API.
</documents>

<task>
Implementa el lado servidor de HU16: un nuevo módulo `speech` que expone `POST /speech/token`, protegido por JWT, que devuelve `{token, region, expires_in_seconds}` obtenido desde el STS de Azure AI Speech, con límite de 30 solicitudes por hora por `user_id` y degradación controlada (HTTP 503) cuando el proveedor no está configurado o falla.
</task>

<instructions>
Trabaja de adentro hacia afuera y escribe las pruebas junto al código:

1. **Configuración** (`app/config.py`, `backend/.env.example`):
   - Añade `azure_speech_key: SecretStr | None = None`, `azure_speech_region: str | None = None`, `azure_speech_token_timeout_seconds: float = 5.0`. Deben ser opcionales: la app arranca sin ellas.
   - Documenta las variables en `.env.example` con valores vacíos (nunca un secreto real).
2. **Dominio** (`app/modules/speech/domain/`): dataclass inmutable `SpeechToken(token: str, region: str, expires_in_seconds: int)` con `expires_in_seconds` ≤ 600; errores propios `SpeechUnavailableError` (code `SPEECH_SERVICE_UNAVAILABLE`) y `SpeechRateLimitError` (code `SPEECH_RATE_LIMITED`). Sin imports de FastAPI, Pydantic, httpx ni Redis.
3. **Aplicación** (`app/modules/speech/application/`):
   - Puerto `SpeechTokenProvider(Protocol)` con `async def issue(self) -> SpeechToken`.
   - Caso de uso `IssueSpeechToken` con método `execute(user_id: UUID) -> SpeechToken`: primero incrementa el contador `speech:token:{user_id}` con ventana de 3600 s usando el `RateLimiter` existente; si supera 30 → `SpeechRateLimitError`; luego delega en el proveedor.
4. **Infraestructura** (`app/modules/speech/infrastructure/`): adaptador `AzureSpeechTokenProvider` que hace `POST https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken` con cabecera `Ocp-Apim-Subscription-Key`, timeout configurado, y devuelve `SpeechToken(token, region, 600)`. Traduce: credenciales ausentes, timeout, error de red o status ≠ 200 → `SpeechUnavailableError`. Nunca registres en logs la clave ni el token.
5. **API** (`app/modules/speech/api/`): router `POST /speech/token` con esquema de entrada vacío `extra="forbid"` (rechaza cualquier campo con 422), esquema de salida `SpeechTokenOut`, `user_id` tomado **solo** del JWT. Traducción de errores: `SpeechRateLimitError` → 429, `SpeechUnavailableError` → 503, ambos con cuerpo `{code, message}` según el formato de errores del proyecto. Añade `Cache-Control: no-store` a la respuesta.
6. **Composición**: ensambla el caso de uso en `composition.py` y registra el router en `main.py`.
7. **Contrato**: exporta `backend/openapi.json` actualizado con el script existente en `backend/scripts/`.
</instructions>

<constraints>
- El cliente HTTP para Azure requiere `httpx`, que hoy solo está en el grupo `dev` de `pyproject.toml`. Según `AGENTS.md` no agregues ni muevas dependencias sin preguntar: **detente y pide autorización** para mover `httpx` a `dependencies` antes de escribir el adaptador.
- No crees tablas ni migraciones: esta historia no persiste nada en PostgreSQL.
- Nada de `datetime.now()`/`date.today()` en dominio o aplicación; usa `Clock` si necesitas tiempo.
- No uses el SDK de voz en el backend; solo el endpoint REST de STS.
- No implementes nada marcado como "Fuera de alcance" en HU16 (configuración manual de región/clave, métricas de uso, voz offline).
</constraints>

<tests>
Cubre cada regla y escenario Gherkin con al menos una prueba:
- `tests/unit/speech/`: `IssueSpeechToken` con fakes (`FakeRateLimiter`, `FakeSpeechTokenProvider`): emisión exitosa, intento 31 → `SpeechRateLimitError` sin llamar al proveedor, proveedor caído → `SpeechUnavailableError`.
- `tests/integration/speech/`: endpoint con `httpx.MockTransport` simulando Azure + Redis real de `docker compose`: 200 con `token`/`region`/`expires_in_seconds` y sin la clave en la respuesta; 401 sin JWT; 422 con body extra; 429 tras 30 solicitudes; 503 sin credenciales; 503 por timeout.
- `tests/security/`: la respuesta y los logs capturados (`caplog`) no contienen el valor de `AZURE_SPEECH_KEY`.
- Recomendado: `tests/acceptance/features/speech/token.feature` con pytest-bdd reutilizando los escenarios Gherkin de HU16.
</tests>

<stop_conditions>
Detente y pregunta antes de continuar si:
- Necesitas mover/añadir una dependencia (caso esperado: `httpx`).
- El formato de errores existente no permite un `code` distinto para 429/503.
- Una prueba existente falla por algo que no tocaste.
- Detectas contradicción entre `docs/MVP2.md`, `BLUEPRINT.md` y `AGENTS.md`.
</stop_conditions>

<workflow>
1. Lee la historia y el código de `auth` (rate limiter y deps) y `composition.py`.
2. Presenta un plan corto por capa (archivos a crear/modificar) y espera aprobación.
3. Implementa dominio → aplicación → infraestructura → API con sus pruebas.
4. Ejecuta en `backend/`: `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` y déjalos en verde.
</workflow>

<output_format>
Entrega el reporte exacto definido en `AGENTS.md` (Historia, Cambios, Pruebas y cobertura, Criterio → prueba, Comandos ejecutados, Pendientes). Indica explícitamente que FrontFinanzas debe regenerar su cliente con `ng-openapi-gen`.
</output_format>

<verification>
Antes de reportar, comprueba:
- [ ] `POST /speech/token` devuelve solo `token`, `region`, `expires_in_seconds` (≤ 600).
- [ ] La clave nunca aparece en respuestas, logs, `openapi.json` ni `.env.example`.
- [ ] 401, 422, 429 y 503 cubiertos con pruebas.
- [ ] `user_id` proviene únicamente del JWT.
- [ ] El dominio no importa FastAPI/Pydantic/httpx/Redis; ruff, mypy y pytest en verde.
</verification>
```

### 5.2. Prompt HU17 — Registrar movimiento mediante dictado de voz

```xml
<role>
Eres un ingeniero backend senior experto en FastAPI, arquitectura hexagonal, sincronización offline-first (outbox push/pull) y pruebas de contrato con pytest y pytest-bdd. Priorizas no romper reglas de dominio ya cerradas.
</role>

<context>
Repositorio: BackFinanzas (rama `dev`). HU16 ya está implementada (`POST /speech/token`).
En HU17 el usuario dicta un gasto/ingreso en la PWA; el frontend (repositorio FrontFinanzas) transcribe con `SpeechRecognizer`, interpreta el texto a un borrador, el usuario confirma y el movimiento se guarda en Dexie + `outbox`. Ese movimiento llega al backend por el **flujo de sincronización existente** (`app/modules/sync` → `push` → `app/modules/transactions/application/upsert.py`), exactamente igual que uno creado manualmente (HU04/HU05).
Por tanto, el trabajo backend de HU17 NO es crear un endpoint nuevo, sino **garantizar y demostrar con pruebas** que los movimientos producidos por dictado cumplen el contrato y las reglas actuales, y que el token de voz sirve para el reconocimiento.
</context>

<documents>
- `docs/MVP2.md` → sección `#### HU17. Registrar movimiento mediante dictado de voz` (en especial la tabla de interpretación de la regla 4 y los escenarios Gherkin).
- `BLUEPRINT.md` → solo `#### HU04`, `#### HU05`, `#### HU08` (`name_key`) y `#### HU14` (alertas de presupuesto), más el modelo de datos de movimientos.
- `AGENTS.md`.
- Código: `app/modules/transactions/{domain,application}`, `app/modules/sync/application/push.py`, `tests/unit/transactions/`, `tests/acceptance/features/sync/movimientos.feature`.
</documents>

<task>
Implementa el lado servidor de HU17 como pruebas de regresión y contrato sobre el flujo existente, corrigiendo el backend solo si alguna prueba revela una brecha frente a las reglas de HU04/HU05/HU17.
</task>

<instructions>
1. **Análisis previo:** revisa las reglas de dominio de `transactions` (`rules.py`, `entities.py`, `errors.py`) y confirma que validan: `amount_minor` entero > 0 y ≤ 13 dígitos, `type` en {`expense`, `income`}, categoría activa del mismo tipo y del mismo `user_id`, `occurred_on` no futura según `Clock`, `description` ≤ 100 caracteres.
2. **Pruebas de aceptación** (`tests/acceptance/features/speech/dictado.feature` + steps con pytest-bdd), traduciendo los escenarios de HU17 a payloads de `push`:
   - "Gasté veinticinco mil pesos en almuerzo en Alimentación" → push con `type=expense`, `amount_minor=2500000`, categoría "Alimentación", `description="Almuerzo"`, fecha de hoy → aceptado y visible en `pull` con `version` asignada por el servidor.
   - "Recibí tres millones quinientos mil pesos de Salario" → `type=income`, `amount_minor=350000000` → aceptado.
   - Borrador sin monto o con monto 0/negativo → rechazado con el error de dominio existente (sin crear registro).
   - Fecha futura → rechazado con el error existente.
   - Reenvío del mismo UUID (doble pulsación de "Guardar" / reintento de outbox) → idempotente, no duplica.
3. **Pruebas unitarias** de `UpsertTransaction` solo para casos límite de HU17 no cubiertos hoy (descripción de 100 vs 101 caracteres, monto de 13 vs 14 dígitos, categoría de tipo opuesto).
4. **Contrato de voz:** añade una prueba de integración que confirme que `POST /speech/token` es reutilizable para STT (la respuesta contiene `region` utilizable con `SpeechConfig.fromAuthorizationToken`) sin parámetros adicionales.
5. Si alguna prueba falla por una brecha real del backend, corrígela en la capa correcta (dominio primero) y documenta el porqué en el reporte.
</instructions>

<constraints>
- **No** agregues campos nuevos al modelo (`source="voice"`, transcripción, audio, etc.) ni migraciones: el dictado no cambia el modelo de datos. Si crees que hace falta, detente y pregunta.
- **No** crees un endpoint de parsing de texto en el servidor: la interpretación del dictado es dominio puro del frontend según `docs/MVP2.md`.
- No almacenes ni registres transcripciones de voz en el backend.
- No debilites validaciones existentes para que un caso de voz pase.
- Fuera de alcance: guardado automático, edición/eliminación por voz, recurrentes (HU09), etiquetas (HU10), wake-word.
</constraints>

<stop_conditions>
Detente y pregunta si: una regla de HU17 contradice HU04/HU05 en `BLUEPRINT.md`; la corrección requiere cambiar el protocolo de sincronización o el modelo; o una prueba existente falla por algo que no tocaste.
</stop_conditions>

<workflow>
1. Lee historia, reglas de dominio y pruebas existentes de `transactions` y `sync`.
2. Presenta un plan corto (pruebas a crear y posibles correcciones) y espera aprobación.
3. Escribe las pruebas primero; implementa correcciones solo si alguna falla por una brecha real.
4. Ejecuta `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` en `backend/` y déjalo en verde.
</workflow>

<output_format>
Reporte según `AGENTS.md`. Añade una tabla "Escenario HU17 → prueba backend" y la lista de tareas que quedan para FrontFinanzas (parser `parseVoiceTransactionDraft`, `SpeechRecognitionService`, UI "Dictar movimiento").
</output_format>

<verification>
- [ ] Cada escenario Gherkin de HU17 con impacto en servidor tiene una prueba.
- [ ] `amount_minor` siempre entero en centavos; sin `float`.
- [ ] Idempotencia por UUID verificada.
- [ ] Sin cambios de modelo, migraciones ni endpoints nuevos (o justificados y aprobados).
- [ ] ruff, mypy y pytest en verde.
</verification>
```

### 5.3. Prompt HU18 — Escuchar detalle de un movimiento en voz alta

```xml
<role>
Eres un ingeniero backend senior experto en FastAPI, seguridad de APIs y pruebas de contrato. Distingues qué responsabilidad pertenece al cliente y cuál al servidor, y evitas sobreconstruir.
</role>

<context>
Repositorio: BackFinanzas (rama `dev`). HU16 y HU17 ya están implementadas.
En HU18 el usuario pulsa "Escuchar movimiento" y la PWA (FrontFinanzas) formatea el movimiento a texto en español con `formatTransactionForSpeech` y lo sintetiza con `SpeechSynthesizer` usando el token temporal de `POST /speech/token`. Los datos se leen desde Dexie (local), no desde un endpoint nuevo.
El backend solo participa emitiendo el token. El objetivo es **asegurar que el contrato y las políticas de HU16 soportan correctamente el uso TTS** (lecturas frecuentes, reutilización del token, errores claros), sin añadir superficie innecesaria.
</context>

<documents>
- `docs/MVP2.md` → secciones `#### HU18` y `#### HU16`.
- `AGENTS.md`.
- Código: `app/modules/speech/**` y sus pruebas en `tests/`.
</documents>

<task>
Verifica y, si es necesario, ajusta el módulo `speech` para cubrir el uso Text-to-Speech de HU18, documentando el contrato para el frontend.
</task>

<instructions>
1. **Pruebas de contrato TTS** (`tests/integration/speech/test_speech_tts_contract.py`):
   - El token emitido es independiente del uso (STT o TTS): una sola llamada sirve para ambos; el endpoint no acepta un parámetro `mode`/`voice` (422 por `extra="forbid"`).
   - Escenario "Fallo del servicio de síntesis": cuando Azure STS falla, la respuesta es 503 con `code="SPEECH_SERVICE_UNAVAILABLE"` y `message` en español, apta para que el cliente muestre "No se pudo reproducir el movimiento. Intenta nuevamente".
   - La respuesta incluye `Cache-Control: no-store` y no expone la clave.
2. **Documentación OpenAPI:** completa `summary`, `description` y `responses` (200, 401, 422, 429, 503) del endpoint en el router para que `ng-openapi-gen` genere tipos de error útiles; vuelve a exportar `backend/openapi.json`.
3. **Prueba de aceptación** (`tests/acceptance/features/speech/lectura.feature`): "Obtener autorización para leer un movimiento" (200) y "Servicio de síntesis no disponible" (503).
4. Si encuentras huecos en HU16 que afecten HU18 (p. ej. falta `no-store`, mensajes en inglés, códigos de error inconsistentes), corrígelos en la capa correspondiente y justifícalo.
</instructions>

<constraints>
- **No** crees endpoints de síntesis en el servidor, ni proxies de audio, ni endpoints para leer un movimiento "formateado": el formateo es dominio puro del frontend y los datos salen de Dexie.
- No cambies la vigencia (600 s), el límite (30/h) ni la forma de la respuesta de `POST /speech/token`.
- No selecciones voz (`es-CO-SalomeNeural`) en el backend; es configuración del cliente.
- Fuera de alcance: descarga MP3, selección de voces/velocidades, lectura de gráficos (HU15) o presupuestos (HU14).
</constraints>

<stop_conditions>
Detente y pregunta si consideras necesario que el backend devuelva voz/locale, si el límite de 30/h parece insuficiente para el uso TTS esperado, o si una prueba existente falla por algo que no tocaste.
</stop_conditions>

<workflow>
1. Lee HU18 y el módulo `speech`.
2. Presenta un plan corto y espera aprobación.
3. Escribe pruebas, ajusta solo lo necesario y exporta `openapi.json`.
4. Ejecuta `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` en `backend/`.
</workflow>

<output_format>
Reporte según `AGENTS.md`, más una sección "Contrato para FrontFinanzas" con un ejemplo de respuesta 200 y de error 503 (sin token real) y la lista de tareas frontend pendientes (`formatTransactionForSpeech`, `SpeechSynthesisService`, botón "Escuchar movimiento"/"Detener lectura").
</output_format>

<verification>
- [ ] Sin endpoints nuevos ni cambios en el modelo de datos.
- [ ] 200/401/422/429/503 documentados en OpenAPI y probados.
- [ ] Mensajes de error en español con `code` estable.
- [ ] ruff, mypy y pytest en verde.
</verification>
```

### 5.4. Prompt HU19 — Escuchar listado de movimientos del historial en voz alta

```xml
<role>
Eres un ingeniero backend senior experto en FastAPI, Redis, rate limiting y rendimiento de APIs, con criterio para validar cuotas frente a patrones de uso reales del cliente.
</role>

<context>
Repositorio: BackFinanzas (rama `dev`). HU16, HU17 y HU18 ya están implementadas.
En HU19 la PWA (FrontFinanzas) lee en voz alta, en bloques de hasta 10, los movimientos visibles del historial (datos de Dexie), con controles Pausar/Reanudar/Siguiente/Detener. Durante una lectura larga, `SpeechAuthService` del cliente renueva el token cuando faltan < 60 s para expirar y reutiliza peticiones en vuelo.
En el backend esto significa: **renovaciones y solicitudes concurrentes de token** deben comportarse de forma predecible bajo la cuota de 30/h, y el historial que el cliente lee debe ser consistente con lo sincronizado (movimientos con `deleted_at` no deben reaparecer como activos).
</context>

<documents>
- `docs/MVP2.md` → secciones `#### HU19` y `#### HU16`.
- `BLUEPRINT.md` → solo `#### HU11` (historial) y `#### HU12` (búsqueda) para entender el origen de los datos.
- `AGENTS.md`.
- Código: `app/modules/speech/**`, `app/modules/sync/application/pull.py`, `app/modules/auth/infrastructure/rate_limiter.py`.
</documents>

<task>
Valida con pruebas que el backend soporta el patrón de uso de HU19 (lectura secuencial larga con renovación de token y borrados lógicos) y corrige únicamente las brechas encontradas.
</task>

<instructions>
1. **Cuota bajo renovación** (`tests/integration/speech/test_speech_rate_limit_renewal.py`):
   - Simula una sesión de lectura de 1 hora con renovaciones cada ~540 s → total muy por debajo de 30 → todas 200.
   - Solicitudes concurrentes (`asyncio.gather` de 5 peticiones del mismo usuario) → el contador de Redis se incrementa de forma atómica (exactamente 5) sin condiciones de carrera.
   - Usuarios distintos tienen cuotas independientes (`speech:token:{user_id}`).
   - Al superar 30 → 429 con `code="SPEECH_RATE_LIMITED"`; tras expirar la ventana (Redis con TTL controlado), vuelve a 200.
2. **Consistencia de datos leídos** (`tests/acceptance/features/speech/historial.feature` con pytest-bdd): tras un `push` que borra lógicamente un movimiento, el `pull` lo devuelve con `deleted_at` (para que el cliente lo omita de la cola de lectura) y nunca lo borra físicamente.
3. **Resiliencia:** un fallo de Azure durante una renovación devuelve 503. Verifica si ese intento consume cuota y que coincide con lo definido en HU16; si HU16 no lo define, pregunta antes de decidir.
4. Corrige en la capa correcta cualquier brecha (p. ej. incremento no atómico, clave de cuota compartida entre usuarios) y explícala en el reporte.
</instructions>

<constraints>
- **No** crees endpoints de historial o lectura por lotes en el servidor: la cola de lectura (`buildHistorySpeechQueue`) es dominio del frontend sobre Dexie.
- No cambies el límite de 30/h ni la vigencia de 600 s sin aprobación.
- No modifiques el protocolo de sincronización ni el modelo de datos.
- Fuera de alcance: lectura automática al abrir la app, barge-in por micrófono, lectura completa de 2.000 registros sin bloques.
</constraints>

<stop_conditions>
Detente y pregunta si: las pruebas demuestran que 30/h es insuficiente para el uso descrito; no está definido si un 503 de Azure consume cuota; o una prueba existente falla por algo que no tocaste.
</stop_conditions>

<workflow>
1. Lee HU19, el módulo `speech`, el rate limiter y `pull.py`.
2. Presenta un plan corto y espera aprobación.
3. Escribe las pruebas; corrige solo brechas reales.
4. Ejecuta `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` en `backend/` y déjalo en verde.
</workflow>

<output_format>
Reporte según `AGENTS.md`, más la lista de tareas que quedan para FrontFinanzas (`buildHistorySpeechQueue`, cola en `SpeechSynthesisService`, `VoicePlayerBarComponent`).
</output_format>

<verification>
- [ ] Renovación, concurrencia, aislamiento por usuario y reinicio de ventana probados.
- [ ] Borrados lógicos verificados vía `pull`; sin borrado físico.
- [ ] Sin endpoints nuevos ni cambios de modelo o de protocolo.
- [ ] ruff, mypy y pytest en verde.
</verification>
```

---

## 6. Implementación realizada en BackFinanzas (HU16–HU19)

> Resultado de ejecutar los prompts de la sección 5 sobre la rama `dev`. Alcance: **solo backend**. El parser de dictado, la síntesis de voz, la cola de lectura y la UI quedan pendientes en FrontFinanzas (ver 6.6).

### 6.1. Resumen general

| HU | Qué se desarrolló en el backend | Código de producción |
|---|---|---|
| HU16 | Nuevo módulo `speech` con `POST /speech/token`: emite un token temporal de Azure AI Speech (600 s) a usuarios autenticados, con límite de 30 por hora por usuario en Redis, degradación a 503 y sin exponer la clave. | Sí |
| HU17 | Se verificó que un movimiento dictado y confirmado entra por `sync/push` con las mismas reglas de HU04/HU05 (monto en centavos, fecha no futura, categoría del mismo tipo, idempotencia por UUID) y que el token sirve para el reconocimiento. Las reglas ya existían: no hubo que cambiar el dominio de `transactions`. | No (solo pruebas) |
| HU18 | Se verificó y documentó en OpenAPI que el mismo token sirve para la síntesis, que el backend no recibe voz ni modo (422) y que un fallo del proveedor llega como 503 con mensaje en español. | No (solo pruebas y documentación del contrato) |
| HU19 | Se verificó la cuota bajo renovaciones de lecturas largas, la atomicidad con peticiones concurrentes (Redis real), el aislamiento por usuario, el reinicio de la ventana y que los movimientos borrados llegan con `deleted: true` en el pull para omitirlos de la lectura. | No (solo pruebas) |

### 6.2. Arquitectura del módulo `speech`

```
backend/app/modules/speech/
├── domain/          SpeechToken (inmutable, vigencia 1–600 s, repr sin token)
│                    SpeechUnavailableError → 503 SPEECH_SERVICE_UNAVAILABLE
│                    SpeechRateLimitError   → 429 SPEECH_RATE_LIMITED
├── application/     Puertos SpeechTokenProvider y RequestCounter (Protocol)
│                    Caso de uso IssueSpeechToken.execute(user_id)
├── infrastructure/  AzureSpeechTokenProvider (httpx → STS /sts/v1.0/issueToken)
└── api/             POST /speech/token, SpeechTokenIn (extra="forbid"), SpeechTokenOut, ErrorOut
```

- **Composición:** `app/composition.py` crea el proveedor de Azure desde `Settings` y reutiliza `RedisRateLimiter` de `auth` como contador (el único lugar que cruza módulos). El router se registra en `app/main.py`.
- **Errores:** se añadió `ServiceUnavailableError` en `app/shared/errors.py`; el manejador global de `main.py` la traduce a HTTP 503 con el mismo cuerpo `{code, message}`.
- **Configuración:** `AZURE_SPEECH_KEY` (`SecretStr`), `AZURE_SPEECH_REGION` y `AZURE_SPEECH_TOKEN_TIMEOUT_SECONDS` son opcionales; sin ellas la API arranca y el endpoint responde 503. Documentadas vacías en `backend/.env.example`.
- **Dependencias:** `httpx` pasó del grupo `dev` a dependencias de ejecución (ya estaba en `uv.lock`; no se agregaron librerías nuevas).

### 6.3. Contrato `POST /speech/token`

| Caso | Respuesta |
|---|---|
| Sesión válida, cuerpo vacío u omitido | `200` `{"token": "<jwt-de-azure>", "region": "eastus", "expires_in_seconds": 600}` + `Cache-Control: no-store` |
| Sin `Authorization` o JWT inválido | `401` |
| Cualquier campo en el cuerpo (`user_id`, `voice`, `mode`, `key`…) | `422` |
| Más de 30 solicitudes en la última hora (por `user_id` del JWT) | `429` `{"code": "SPEECH_RATE_LIMITED", "message": "Has alcanzado el límite temporal del servicio de voz. Intenta más tarde"}` |
| Azure sin configurar, timeout, error de red o respuesta ≠ 200 | `503` `{"code": "SPEECH_SERVICE_UNAVAILABLE", "message": "El servicio de voz no está disponible en este momento"}` |

`backend/openapi.json` se regeneró con `scripts/export_openapi.py`; FrontFinanzas debe regenerar su cliente con `ng-openapi-gen`.

### 6.4. Decisiones tomadas

1. **Un intento que termina en 503 consume cuota:** el contador sube antes de llamar a Azure, para que un cliente que reintenta en bucle no sature el proveedor. Con renovaciones cada ~540 s, una hora de lectura usa unos 7 tokens de 30.
2. **El backend no elige voz ni idioma:** la voz (`es-CO-SalomeNeural`) y el locale (`es-CO`) son configuración del cliente; el token es único para STT y TTS.
3. **Sin cambios de modelo de datos, migraciones ni protocolo de sincronización:** el dictado y la lectura reutilizan `sync/push` y `sync/pull` tal como están.
4. **Seguridad:** la clave solo se lee con `get_secret_value()` al llamar a Azure; los logs registran solo el tipo de error o el código HTTP, nunca la clave ni el token.

**Cambio de regla aprobado y aplicado** en `AGENTS.md` y `BLUEPRINT.md` (convenciones): "Errores de dominio… HTTP 422" ahora incluye las excepciones `UnauthorizedError` → 401, `TooManyRequestsError` → 429 y `ServiceUnavailableError` → 503, y deja explícito que los límites de uso cuentan cada intento, también los que terminan en 503.

### 6.5. Pruebas y trazabilidad

| Criterio | Prueba que lo verifica |
|---|---|
| HU16 — Obtención exitosa de token | `tests/integration/speech/test_speech_api.py › test_obtencion_exitosa_de_token_temporal`; `features/speech/token.feature` |
| HU16 — Límite excedido (429) | `test_speech_api.py › test_limite_de_solicitudes_excedido`; `unit/speech/test_issue_token.py › test_la_cuota_es_de_30_por_hora_por_usuario` |
| HU16 — Servicio no configurado o caído (503) | `test_speech_unavailable.py` (500, 401 de Azure, timeout, sin credenciales); `unit/speech/test_azure_provider.py` |
| HU16 — Sin sesión / campos extra | `test_speech_api.py › test_sin_sesion_responde_401`, `test_campos_extra_se_rechazan_con_422` |
| HU16 — Clave nunca expuesta | `tests/security/test_speech_security.py`; `test_azure_provider.py › test_los_logs_no_contienen_la_clave_ni_el_token` |
| HU17 — Gasto e ingreso dictados se sincronizan | `features/speech/dictado.feature` (2.500.000 y 350.000.000 centavos) |
| HU17 — Monto 0, fecha futura, categoría de otro tipo | `dictado.feature` (`InvalidAmountError`, `FutureDateError`, `CategoryTypeMismatchError`) |
| HU17 — Doble "Guardar" no duplica | `dictado.feature › Pulsar dos veces "Guardar"…` |
| HU18 — Mismo token para síntesis, sin voz en el backend | `test_speech_tts_contract.py`; `features/speech/lectura.feature` |
| HU18 — Fallo del servicio de síntesis | `test_speech_tts_contract.py › test_fallo_del_servicio_de_sintesis` |
| HU18 — OpenAPI documenta 200/401/422/429/503 | `test_speech_tts_contract.py › test_openapi_documenta_todas_las_respuestas` |
| HU19 — Renovaciones en lectura larga | `test_issue_token.py › test_renovar_cada_540_segundos…`; `features/speech/historial.feature` |
| HU19 — Concurrencia atómica y reinicio de ventana (Redis real) | `test_speech_rate_limit_renewal.py` |
| HU19 — Cuotas independientes por usuario / 503 consume cuota | `test_issue_token.py` |
| HU19 — Movimiento borrado llega con `deleted: true` | `historial.feature` |

**Estado de la verificación (local, sin Docker):**
- `ruff check`, `ruff format --check`, `mypy app` (estricto): ✅
- `pytest` de unitarias completas + API y seguridad de `speech`: ✅ 241 pruebas en verde; cobertura del módulo `speech`: 99 %.
- `scripts/export_openapi.py --check`: ✅
- **Pendiente de ejecutar** (requiere PostgreSQL y Redis de `docker compose up -d`, o la CI): las 15 features de `tests/acceptance/features/speech/` y `test_speech_rate_limit_renewal.py`. Se recolectan sin errores (`pytest --collect-only`).

### 6.6. Implementación en FrontFinanzas (rama `dev`)

La interfaz de voz quedó integrada con el frontend existente (Angular 22, componentes standalone `OnPush` con signals, Dexie + `outbox`) sin cambiar el flujo manual ni el modelo de datos.

**Arquitectura**

```
src/app/core/speech/
├── speech-engine.ts           Puerto SpeechEngine + SPEECH_LOCALE (es-CO) y SPEECH_VOICE (es-CO-SalomeNeural)
├── azure-speech-engine.ts     Adaptador de microsoft-cognitiveservices-speech-sdk (SpeechRecognizer,
│                              SpeechSynthesizer + SpeakerAudioDestination para pausar/reanudar)
├── speech-auth.service.ts     Token temporal solo en memoria, ligado a la cuenta; renueva con < 60 s;
│                              peticiones simultáneas compartidas; 429/503/sin red → SpeechError
├── speech-recognition.service.ts  Dictado: permiso de micrófono, estados Listo/Escuchando/Procesando,
│                              doble toque detiene, pérdida de red cancela y libera el micrófono
├── speech-synthesis.service.ts    Lectura única exclusiva y cola con pausar/reanudar/siguiente/detener
├── speech-errors.ts           SpeechError + textos exactos de este documento
└── speech-sdk.d.ts            Declaración del bundle de navegador del SDK
src/app/features/movimientos/
├── domain/voice.ts            parseVoiceTransactionDraft, formatTransactionForSpeech, buildHistorySpeechQueue
├── components/voice-player-bar.ts  Barra de lectura del historial
└── pages/                     transaction-form (dictar / escuchar) e history (escuchar historial)
```

| HU | Qué ve el usuario |
|---|---|
| HU16 | Nada directamente: cualquier acción de voz obtiene el token de `POST /speech/token` (método `Api.speechToken()`). Sin conexión no se llama a la API y se muestra el aviso correspondiente. |
| HU17 | En "Nuevo movimiento", el botón **"Dictar movimiento"** con estado accesible (`aria-live`). El dictado prellena tipo, monto, categoría, fecha y descripción; si falta el monto, avisa "No pudimos detectar el monto. Ingrésalo para continuar" y "Guardar" queda deshabilitado. Siempre guarda el usuario con el mismo `repo.save` (Dexie + `outbox`) y las alertas de presupuesto de siempre. |
| HU18 | Al abrir un movimiento, el botón **"Escuchar movimiento"**, que cambia a **"Detener lectura"** mientras suena. Lee los datos locales: "Gasto de $25.000 en la categoría Alimentación, registrado hoy, concepto: Almuerzo". |
| HU19 | En "Movimientos", el botón **"Escuchar historial"** lee los movimientos filtrados en bloques de 10, resalta la fila que se está leyendo y muestra la barra con Pausar/Reanudar, Siguiente y Detener. Al terminar un bloque ofrece "Escuchar los siguientes". Cambiar filtros o salir de la pantalla detiene la lectura. |

**Decisiones técnicas**
- **SDK:** `microsoft-cognitiveservices-speech-sdk@^1.53.0`, el único SDK autorizado en este documento. Se carga con `import()` diferido la primera vez que se usa la voz (chunk aparte de ~65 kB comprimido), así que el bundle inicial no crece. Se usa el bundle oficial para navegador porque la entrada principal del paquete arrastra módulos de Node (`https`, `url`); se declaró en `allowedCommonJsDependencies`.
- **Seguridad:** nada de claves en `environment.ts`; el token vive solo en memoria y no se reutiliza si cambia la cuenta.
- **Capas:** los componentes usan servicios, nunca el SDK; el dominio de voz es puro (recibe la fecha de hoy del `Clock`) y la descripción conserva las tildes originales del dictado.

**Verificación:** `tsc` ✅ · ESLint ✅ · `ng test`: 138 pruebas en verde (31 de dominio de voz y 23 de servicios de voz con un motor falso) ✅ · `ng build` de producción sin advertencias ✅. El CLI de Angular 22 exige Node ≥ 22.22.3; en la máquina de desarrollo hay Node 22.19.0, así que los comandos se ejecutaron con `npx -p node@24`.

**Pendiente:** probarlo de punta a punta en un navegador real con una clave de Azure AI Speech configurada en el backend (`AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`). Las pruebas automáticas sustituyen el SDK por un motor falso.
