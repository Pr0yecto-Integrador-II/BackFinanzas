# Reportes y discusión del MVP 2

Este documento organiza el **flujo de trabajo con la IA** durante el MVP 2 de voz (HU16–HU19):

- **§1–§4 Reportes de corrección:** ajustes que el equipo pide sobre lo que entregó la IA (C-01 en §2, C-02 en §3, C-03 en §4). No son historias de usuario nuevas: cada uno se plantea como un **prompt de corrección**, con su motivo, lo esperado y el resultado.
- **§5 Discusión:** en orden, lo que pidió el equipo, lo que preguntó o propuso la IA, lo que respondió el equipo y la decisión que quedó.

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
| C-01 | 2026-11-10 | Frontend (voz) | La voz está repartida en botones por pantalla; no hay un punto de entrada único ni comandos en lenguaje natural, y la confirmación solo se hace tocando "Guardar". | Ajuste funcional y de experiencia | Pendiente de registrar resultado (§2.6) |
| C-02 | 2026-11-10 | Frontend (voz) | Tras C-01, el asistente responde "no te entendí" con demasiada frecuencia: no reconoce bien instrucciones comunes como "léeme el último gasto" o "el último ingreso". | Ajuste de precisión y experiencia | Pendiente |
| C-03 | 2026-11-10 | Frontend (voz) | Al registrar un gasto por voz, el usuario responde "sí" a la confirmación, pero el asistente no continúa: no guarda o no le dice que ya lo registró. | Defecto (prioridad alta, antes que C-02) | Pendiente |

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

## 3. C-02 — Precisión del asistente: entender casi cualquier solicitud

### 3.1. Resultado entregado por la IA

- El asistente de voz global de C-01 interpreta la frase con reglas locales y, cuando ninguna coincide, responde "no te entendí".
- En las pruebas del equipo, solicitudes comunes caen en esa respuesta, por ejemplo "léeme el último gasto" y "el último ingreso".

> Nota: al 2026-11-10 el código del asistente de C-01 no está en `origin/dev` de FrontFinanzas (el último commit allí es `056c5cf`). El prompt de C-02 le pide al agente localizarlo y detenerse si no existe.

### 3.2. Observación del equipo

> "No está reconociendo lo que le digo correctamente y solo dice 'no te entendí'. ¿Puedes hacer algo para que entienda mejor todas las instrucciones que le dé? Como 'léeme el último gasto', 'el último ingreso', todas las posibles solicitudes que haga un usuario: debes poder predecirlas para no caer tanto en esa respuesta de 'no entendí', porque eso puede ser frustrante para el usuario. Así que necesitamos que sea casi perfecto."

### 3.3. Diagnóstico

Causas probables que el prompt pide comprobar en el código antes de cambiar nada:

| Capa | Problema probable | Ejemplo que falla |
|---|---|---|
| Reconocimiento (Azure) | Solo se usa la mejor transcripción y el SDK no conoce el vocabulario de la app (categorías, "ingreso", "gasto", nombres propios). | "Léeme el último gusto" en lugar de "gasto" |
| Normalización | No se limpian por igual tildes, signos, mayúsculas, muletillas ("por favor", "oye", "eh") ni números en cifra o palabra. | "Léeme los últimos 5 gastos." frente a "leeme los ultimos cinco gastos" |
| Interpretación | Las reglas exigen frases casi exactas: no cubren el singular ("el último"), los sinónimos ("dime", "muéstrame", "cuáles fueron") ni el orden libre. | "¿Cuál fue mi último ingreso?" |
| Cobertura | No hay intención para solicitudes habituales: totales ("cuánto gasté este mes"), saldo, gastos por categoría o por fecha, repetir, detener. | "¿Cuánto llevo gastado hoy?" |
| Respuesta de error | "No te entendí" no ofrece una salida: ni sugerencia ni ejemplos. | Cualquier frase dudosa |

### 3.4. Decisiones del equipo para el ajuste

1. **Meta medible:** un corpus de al menos 200 frases reales de prueba, con **≥ 95 % de intención correcta** y **0 guardados sin confirmación**. "Casi perfecto" se verifica con números, no a ojo.
2. **Nunca un "no te entendí" seco:**
   - Con duda razonable, el asistente propone su mejor interpretación ("¿Quieres que te lea tu último gasto?") y espera sí o no.
   - Sin ninguna pista, responde con ejemplos de lo que sí puede hacer.
   - Al segundo intento fallido ofrece la vía manual.
3. **Pedidos fuera de alcance:** se reconocen y se responden con una explicación ("Por ahora no puedo eliminar movimientos por voz; ábrelo desde el historial"), no con "no te entendí".
4. **Interpretación local y determinista:** sin LLM ni servicios nuevos, como exige `MVP2.md`. Si después de C-02 la precisión no llega a la meta, se evaluará un servicio de comprensión de lenguaje (por ejemplo Azure CLU) como corrección futura con aprobación previa.
5. **Mejorar también el reconocimiento:** usar del mismo SDK las listas de frases (`PhraseListGrammar`) con el vocabulario y las categorías del usuario, y las transcripciones alternativas (N-best).
6. **Privacidad:** las frases no reconocidas solo se registran en la consola en modo desarrollo; nunca se envían al servidor ni se guardan.

### 3.5. Prompt de corrección

```xml
<role>
Eres un ingeniero frontend senior especializado en interfaces de voz y comprensión de lenguaje natural basada en reglas para español colombiano, con experiencia en Angular 22, Azure AI Speech y pruebas con Vitest. Corriges un resultado ya entregado sin romper lo que funciona y sigues `AGENTS.md`.
</role>

<context>
Repositorio FrontFinanzas, rama `dev`. En la corrección C-01 (`BackFinanzas/docs/REPORTES-Y-DISCUSION.md` §2) entregaste un asistente de voz global con un botón flotante. El equipo lo probó y pide la corrección C-02 (§3 del mismo documento): el asistente responde "no te entendí" con demasiada frecuencia.

Observación textual del equipo:
"No está reconociendo lo que le digo correctamente y solo dice 'no te entendí'. ¿Puedes hacer algo para que entienda mejor todas las instrucciones que le dé? Como 'léeme el último gasto', 'el último ingreso', todas las posibles solicitudes que haga un usuario: debes poder predecirlas para no caer tanto en esa respuesta de 'no entendí', porque eso puede ser frustrante para el usuario. Así que necesitamos que sea casi perfecto."

Código a revisar primero:
- Asistente de C-01: `src/app/features/asistente/` (dominio de intenciones, servicio orquestador y botón flotante).
- `src/app/core/speech/azure-speech-engine.ts` (reconocimiento con `SpeechRecognizer`).
- `src/app/features/movimientos/domain/voice.ts` (`normalizeSpeech`, `wordsToNumber`, `parseVoiceTransactionDraft`).
- Datos locales: `TransactionRepo`, `CategoryRepo`, `BudgetRepo`, `AuthService.currency`, `Clock`.
</context>

<task>
Haz que el asistente entienda casi cualquier solicitud razonable de un usuario y que nunca responda con un "no te entendí" sin ofrecer una salida. La meta es ≥ 95 % de intención correcta sobre un corpus de al menos 200 frases, sin guardar nada sin confirmación.
</task>

<instructions>
1. **Diagnostica antes de cambiar.** Crea un corpus de prueba (`intents.corpus.ts`) con al menos 200 frases reales y su intención y datos esperados. Incluye:
   - Variantes con y sin tildes, signos, mayúsculas y muletillas.
   - Números en cifra y en palabras, singular y plural, y orden libre.
   - Los errores típicos de reconocimiento.
   Mide la precisión actual y repórtala como línea base.
2. **Normalización única.** Una función pura `normalizeUtterance` que:
   - Pase a minúsculas y quite tildes y signos.
   - Elimine muletillas ("por favor", "oye", "eh", "este", "porfa", "me haces el favor de").
   - Convierta números hablados y en cifra con `wordsToNumber`; "el último" o "la última" = 1 y "un par" = 2.
   - Unifique sinónimos de verbos ("léeme", "dime", "muéstrame", "cuéntame", "cuáles fueron", "qué fue") a una forma canónica.
3. **Interpretación por puntuación, no por coincidencia exacta.**
   - Cada intención declara palabras clave con peso y espacios a extraer (tipo, cantidad, periodo, categoría, monto).
   - Gana la intención con mayor puntaje y se calcula una confianza.
   - Tolera errores de reconocimiento con distancia de edición propia (sin dependencias): máximo 1 en palabras de 4 a 6 letras y máximo 2 en las de 7 o más, para verbos clave, "gasto", "ingreso" y nombres de categorías.
4. **Cobertura mínima de intenciones** (todas responden leyendo datos locales de Dexie):

   | Intención | Ejemplos |
   |---|---|
   | Últimos N (gasto, ingreso o todos) | "léeme el último gasto", "el último ingreso", "mis últimos tres movimientos" |
   | Por periodo | "qué gasté hoy", "mis gastos de ayer", "ingresos de esta semana", "gastos del mes" |
   | Por categoría | "mis gastos en transporte", "cuánto llevo en alimentación" |
   | Totales y saldo | "cuánto gasté este mes", "cuánto me ha entrado", "cuál es mi saldo del mes" |
   | Registrar | la existente de C-01, con pistas de categoría ampliadas |
   | Confirmar / cancelar / repetir / detener / ayuda | — |
   | Fuera de alcance reconocido | "elimina el último gasto", "cambia el monto": responde con la explicación y la vía manual |

5. **Desambiguación en lugar de error:**
   - Confianza alta: ejecuta.
   - Confianza media: pregunta "¿Quieres que …?" con su mejor interpretación y espera sí o no.
   - Confianza baja: responde "Puedo leer tus últimos gastos, decirte cuánto llevas este mes o registrar un gasto. ¿Qué necesitas?".
   - Tras dos intentos fallidos seguidos, ofrece la pantalla correspondiente.
6. **Mejor reconocimiento en el adaptador de Azure** (mismo SDK, sin dependencias nuevas):
   - Usa `PhraseListGrammar` con los verbos y comandos del asistente, las categorías activas y las etiquetas del usuario.
   - Pide resultados detallados (`OutputFormat.Detailed`) y prueba la interpretación sobre las transcripciones alternativas (N-best) antes de rendirte.
   - Mantén el puerto `SpeechEngine` para que las pruebas sigan usando el motor falso.
7. **Documentación:**
   - Añade en `BackFinanzas/docs/MVP2.md` §6.8 "Ajuste C-02" con la lista de intenciones soportadas y frases de ejemplo.
   - Completa §3.6 "Resultado de la corrección" en `REPORTES-Y-DISCUSION.md`, con la precisión antes y después.
</instructions>

<constraints>
- Es una corrección, no una historia nueva: no crees HU ni cambies la numeración de `MVP2.md`.
- Sin LLM, sin servicios externos y sin dependencias nuevas. La distancia de edición se implementa en el dominio.
- Sin cambios en el backend, el modelo de datos, Dexie ni el `outbox`.
- Nunca guardar sin confirmación explícita. La desambiguación nunca ejecuta un registro sin el "sí" de C-01.
- Las frases no reconocidas solo se registran en la consola en modo desarrollo; nunca se envían ni se guardan.
- El dominio de intenciones es puro: sin Angular, Dexie ni SDK; la fecha llega desde `Clock`.
</constraints>

<tests>
- Prueba de corpus que falla si la precisión baja de 95 %; imprime la matriz de confusión de las fallas.
- Casos explícitos: "léeme el último gasto" → últimos 1 gasto; "el último ingreso" → últimos 1 ingreso; "léeme el último gusto" → gasto (tolerancia); "Léeme los últimos 5 gastos." y "leeme los ultimos cinco gastos" → mismo resultado.
- Confianza media → pregunta de desambiguación; confianza baja → ejemplos; dos fallas → vía manual.
- Fuera de alcance reconocido → explicación, no "no te entendí".
- El adaptador de Azure configura la lista de frases y usa las alternativas (con un SDK simulado).
- Todas las pruebas existentes de voz (HU16–HU19 y C-01) siguen en verde sin modificarlas.
</tests>

<stop_conditions>
Detente y pregunta si no encuentras el código del asistente de C-01, si la meta de 95 % no se alcanza sin un servicio de NLU externo, si necesitas una dependencia nueva o si una prueba existente falla por algo que no tocaste.
</stop_conditions>

<workflow>
1. Lee este reporte (§2 y §3) y el código indicado.
2. Construye el corpus y mide la línea base.
3. Presenta un plan corto con la línea base y espera aprobación.
4. Implementa normalización → interpretación → desambiguación → reconocimiento, con sus pruebas.
5. Ejecuta `npm run lint`, `npm test` y `npm run build` (Node ≥ 22.22.3) y déjalos en verde.
</workflow>

<output_format>
Reporte con el formato de `AGENTS.md`: Corrección C-02, Cambios, precisión antes/después sobre el corpus, Pruebas, Comandos y resultado, Pendientes. Incluye una tabla con 20 frases representativas, la intención detectada y la respuesta hablada.
</output_format>

<verification>
- [ ] Corpus de ≥ 200 frases con precisión ≥ 95 % (antes y después reportados).
- [ ] "Léeme el último gasto" y "el último ingreso" funcionan.
- [ ] Ningún "no te entendí" sin sugerencia o ejemplos.
- [ ] Ningún guardado sin confirmación.
- [ ] Lista de frases y N-best activos en el adaptador de Azure.
- [ ] `MVP2.md` §6.8 y `REPORTES-Y-DISCUSION.md` §3.6 actualizados.
- [ ] lint, test y build en verde.
</verification>
```

### 3.6. Resultado de la corrección

_Pendiente de ejecutar el prompt. Al aplicarlo, registrar aquí:_

| Campo | Valor |
|---|---|
| Fecha de ejecución | |
| Herramienta / modelo | |
| Commit | |
| Precisión del corpus (antes → después) | |
| Frases representativas y respuesta del asistente | |
| Pruebas (nuevas / totales) | |
| Desviaciones respecto al prompt y su motivo | |
| Estado final de C-02 | |

---

## 4. C-03 — La confirmación por voz no completa el registro

### 4.1. Resultado entregado por la IA

- En el flujo de C-01, el asistente lee el borrador ("Voy a registrar un gasto de … ¿Lo guardo?") y espera la respuesta.
- Cuando el usuario dice "sí", el flujo no avanza: no anuncia "Gasto guardado" y no queda claro si el gasto se guardó.

> Nota: igual que en C-02, el código del asistente de C-01 no está en `origin/dev` de FrontFinanzas al 2026-11-10. El prompt le pide al agente localizarlo y detenerse si no existe.

### 4.2. Observación del equipo

> "Cuando me pide confirmar un gasto que le digo por voz, por más que le digo que 'sí' a la confirmación, no continúa a confirmarme que ya lo registró."

### 4.3. Diagnóstico

El síntoma admite varias causas. El prompt exige reproducirlo con una prueba antes de corregir y revisar cada una:

| # | Causa probable | Cómo se manifiesta |
|---|---|---|
| 1 | **El micrófono no se vuelve a abrir** después de la pregunta: la escucha de la respuesta no se inicia, o se inicia antes de que termine la locución y queda cancelada. | El "sí" nunca llega al asistente. |
| 2 | **"Sí" no se reconoce como confirmación:** Azure devuelve "Sí.", "Si", "Sí, guárdalo" o "Claro", y la comparación es exacta, sin normalizar tildes y signos, o con una lista corta de sinónimos. | El "sí" llega, pero se interpreta como "no entendido". |
| 3 | **La respuesta se interpreta sin contexto:** el "sí" pasa por el interpretador general en lugar de uno específico para el estado `awaiting_confirmation`. | Se ignora o se trata como otra intención. |
| 4 | **Palabras de una sílaba:** el reconocedor de una sola frase descarta a veces respuestas muy cortas como "sí" por silencio inicial o fin de frase prematuro. | El resultado es `NoMatch` o queda vacío. |
| 5 | **El guardado falla en silencio:** `TransactionRepo.save`, las alertas o la locución final lanzan un error que nadie atrapa y la máquina de estados queda detenida. | Nada se anuncia; el gasto puede quedar guardado o no. |
| 6 | **La locución final se corta:** la exclusividad de audio (`SpeechSynthesisService.stop`) o un cambio de estado cancela el "Gasto guardado". | Se guarda, pero no se anuncia. |
| 7 | **Eco:** el micrófono capta la propia pregunta del asistente ("¿Lo guardo?") y la toma como respuesta. | Se interpreta una frase que el usuario no dijo. |

### 4.4. Decisiones del equipo para el ajuste

1. **Prioridad alta:** es un defecto del flujo principal; se corrige antes de C-02.
2. **Interpretación según el estado:** mientras espera confirmación, el asistente solo evalúa confirmar o cancelar, con una lista amplia y normalizada:
   - Confirmar: "sí", "si", "sip", "claro", "dale", "listo", "ok", "okey", "correcto", "eso es", "hágale", "de una", "confirmo", "guárdalo", "afirmativo".
   - Cancelar: "no", "nop", "cancela", "déjalo", "no lo guardes", "espera".
3. **Siempre hay respuesta final hablada y visible:** "Gasto guardado", "Ingreso guardado", "No lo guardé" o "No pude guardar el gasto, inténtalo desde el formulario". Nunca un silencio.
4. **Dos oportunidades:** si no entiende la respuesta, repregunta una vez ("¿Lo guardo? Responde sí o no"). Si vuelve a fallar, cancela sin guardar y lo dice.
5. **Turnos ordenados:** la escucha de la respuesta empieza solo cuando terminó la locución de la pregunta (con una pausa breve, para evitar el eco). El botón "Confirmar" de la pantalla sigue como alternativa.
6. Se mantiene la regla de C-01: **nada se guarda sin confirmación explícita**.

### 4.5. Prompt de corrección

```xml
<role>
Eres un ingeniero frontend senior experto en Angular 22, máquinas de estado con signals, interfaces de voz con Azure AI Speech y depuración guiada por pruebas (primero reproducir, luego corregir). Corriges un defecto sin romper lo que funciona y sigues `AGENTS.md`.
</role>

<context>
Repositorio FrontFinanzas, rama `dev`. En la corrección C-01 (`BackFinanzas/docs/REPORTES-Y-DISCUSION.md` §2) entregaste un asistente de voz global que, al registrar un gasto, lee el borrador, pregunta "¿Lo guardo?" y debe guardar solo con una confirmación explícita.

Defecto reportado (corrección C-03, §4 del mismo documento), textual:
"Cuando me pide confirmar un gasto que le digo por voz, por más que le digo que 'sí' a la confirmación, no continúa a confirmarme que ya lo registró."

Código a revisar:
- Asistente de C-01: `src/app/features/asistente/` (dominio de intenciones, servicio orquestador con su máquina de estados y botón flotante).
- `src/app/core/speech/speech-recognition.service.ts` (`listen()`, estados, cancelación) y `speech-synthesis.service.ts` (`speakOne`, `stop`, exclusividad de audio).
- `src/app/core/speech/azure-speech-engine.ts` (reconocimiento de una sola frase).
- `TransactionRepo.save`, `BudgetRepo.alertsAfterSave`, `SyncService.sync`.
</context>

<task>
Corrige el flujo de confirmación por voz para que, al responder "sí" (o un sinónimo), el gasto o ingreso se guarde y el asistente lo anuncie siempre en voz alta y en pantalla. Ante cualquier otro desenlace también debe responder: cancelado, no entendido o error.
</task>

<instructions>
1. **Reproduce primero.** Escribe una prueba del servicio orquestador con el `SpeechEngine` falso que haga: crear gasto → leer borrador → responder "Sí." → esperar "Gasto guardado" y el registro en Dexie + `outbox`. Debe fallar con el código actual. Anota en el reporte cuál de las causas de §4.3 la provoca (puede ser más de una).
2. **Turnos ordenados:**
   - La escucha de la respuesta empieza solo cuando termina la locución de la pregunta (`await` de la reproducción), con una pausa breve configurable (por ejemplo 300 ms) para evitar el eco.
   - Ninguna llamada a `SpeechSynthesisService.stop()` ni un cambio de estado puede cortar la pregunta o el anuncio final del mismo flujo.
3. **Interpretación según el estado:**
   - En `awaiting_confirmation`, usa un interpretador dedicado `parseConfirmation(transcript)` → `'confirm' | 'cancel' | 'unknown'`, puro.
   - Normaliza tildes, signos y mayúsculas, y acepta frases que empiezan por la respuesta ("sí, guárdalo", "no, espera").
   - Usa las listas de sinónimos de §4.4.
4. **Respuestas cortas:**
   - Agrega "sí", "no" y sus sinónimos a la lista de frases (`PhraseListGrammar`) del reconocimiento de confirmación.
   - Revisa los tiempos de silencio inicial y final del reconocedor para respuestas de una sílaba.
   - Si el resultado es `NoMatch`, cuenta como "no entendido", no como error.
5. **Dos oportunidades:** con "no entendido", repregunta una vez "¿Lo guardo? Responde sí o no". Si vuelve a fallar, responde "No lo guardé" y vuelve a reposo.
6. **Respuesta final garantizada:**
   - Envuelve guardado, alertas y sincronización en manejo de errores.
   - Después de `TransactionRepo.save` anuncia "Gasto guardado" o "Ingreso guardado" y luego las alertas de presupuesto.
   - Si algo falla, anuncia "No pude guardar el gasto, inténtalo desde el formulario" y abre `/movimientos/nuevo` prellenado.
   - La máquina de estados siempre vuelve a `idle`, incluso con errores.
7. **Pantalla:** el panel muestra lo que escuchó en la respuesta y el resultado final. El botón "Confirmar" lleva al mismo camino de guardado.
8. **Documentación:**
   - Añade en `BackFinanzas/docs/MVP2.md` §6.9 "Ajuste C-03" con la causa encontrada y el flujo corregido.
   - Completa §4.6 "Resultado de la corrección" en `REPORTES-Y-DISCUSION.md`.
</instructions>

<constraints>
- Es una corrección, no una historia nueva: no crees HU ni cambies la numeración de `MVP2.md`.
- Nunca guardar sin una confirmación explícita (voz o botón). Un "no entendido" nunca guarda.
- Sin dependencias nuevas ni cambios en el backend, el modelo de datos, Dexie o el `outbox`. El guardado sigue pasando por `TransactionRepo.save`.
- No debilites ni borres pruebas existentes para que pasen.
- Si C-02 ya cambió el interpretador general, el de confirmación sigue siendo independiente y tiene prioridad en `awaiting_confirmation`.
</constraints>

<tests>
- Prueba de regresión del paso 1, ahora en verde.
- `parseConfirmation`: "sí", "Sí.", "si", "sí, guárdalo", "claro", "dale", "ok" → confirm; "no", "No.", "no, espera", "cancela" → cancel; "tal vez", "" → unknown.
- Flujo: confirmar → guarda y dice "Gasto guardado"; cancelar → "No lo guardé" y nada en Dexie; dos "no entendido" → "No lo guardé"; `NoMatch` → repregunta; error en `save` → mensaje de error, formulario prellenado y estado `idle`.
- Turnos: la escucha empieza después de la locución; el anuncio final no se corta.
- Botón "Confirmar" → mismo resultado que el "sí" hablado.
- Las pruebas existentes de voz (HU16–HU19, C-01 y C-02 si existe) siguen en verde sin modificarlas.
</tests>

<stop_conditions>
Detente y pregunta si no encuentras el código del asistente de C-01, si la causa exige tocar el backend o el modelo de datos, si necesitas una dependencia nueva o si una prueba existente falla por algo que no tocaste.
</stop_conditions>

<workflow>
1. Lee este reporte (§2 y §4) y el código indicado.
2. Escribe la prueba de regresión y confirma que falla.
3. Presenta la causa encontrada y un plan corto, y espera aprobación.
4. Corrige, con sus pruebas.
5. Ejecuta `npm run lint`, `npm test` y `npm run build` (Node ≥ 22.22.3) y déjalos en verde.
</workflow>

<output_format>
Reporte con el formato de `AGENTS.md`: Corrección C-03, causa raíz (con la prueba que la demostraba), Cambios, Pruebas, Comandos y resultado, Pendientes. Incluye una tabla con cada respuesta probada ("sí", "Sí.", "claro", "no", silencio…) y lo que hizo el asistente.
</output_format>

<verification>
- [ ] La prueba de regresión fallaba antes y pasa después.
- [ ] Decir "sí" guarda y anuncia "Gasto guardado" o "Ingreso guardado".
- [ ] Cancelar, no entender o un error siempre producen una respuesta hablada y visible, y el estado vuelve a `idle`.
- [ ] Nada se guarda sin confirmación explícita.
- [ ] `MVP2.md` §6.9 y `REPORTES-Y-DISCUSION.md` §4.6 actualizados.
- [ ] lint, test y build en verde.
</verification>
```

### 4.6. Resultado de la corrección

_Pendiente de ejecutar el prompt. Al aplicarlo, registrar aquí:_

| Campo | Valor |
|---|---|
| Fecha de ejecución | |
| Herramienta / modelo | |
| Commit | |
| Causa raíz encontrada (§4.3) | |
| Respuestas probadas y resultado | |
| Pruebas (nuevas / totales) | |
| Desviaciones respecto al prompt y su motivo | |
| Estado final de C-03 | |

---

## 5. Discusión: preguntas de la IA y decisiones del equipo

Registro en orden cronológico de la sesión del 2026-11-10 (Claude Code, modelo Claude Opus 5.5). Las solicitudes y respuestas del equipo se citan textualmente.

### 5.1. Resumen de decisiones

| # | Etapa | Pregunta o propuesta de la IA | Decisión del equipo | Dónde quedó |
|---|---|---|---|---|
| D-01 | Prompts por HU | Los prompts cubren solo el backend; ¿generar también una versión para FrontFinanzas? | No se pidió aparte: el equipo pasó a implementar y luego pidió el frontend (D-05). | `MVP2.md` §5 |
| D-02 | Implementación backend | `httpx` (cliente HTTP para Azure) solo está como dependencia de desarrollo. ¿Moverla a ejecución o usar solo la biblioteca estándar? | **Mover `httpx` a dependencias de ejecución** (recomendada). | `pyproject.toml`, `uv.lock` |
| D-03 | Implementación backend | No hay `uv`, Docker, PostgreSQL ni Redis en la máquina. ¿Cómo verificar? | **Instalar `uv` y verificar parcialmente** (recomendada); las pruebas con BD y Redis quedan para la CI. | `MVP2.md` §6.5 |
| D-04 | Implementación backend | Plan de implementación HU16–HU19 (modo plan, como exige `CLAUDE.md`). | **Plan aprobado** sin cambios. | Commit `8bd6fb8` |
| D-05 | Revisión del backend | Dos decisiones por revisar: (a) ¿un intento que termina en 503 consume cuota? (b) ¿aplicar en `AGENTS.md`/`BLUEPRINT.md` la regla de errores 401/429/503? | **Tomar la opción recomendada y más profesional:** el 503 sí consume cuota y la regla se aplica. Además: **seguir con el frontend**. | `AGENTS.md`, `BLUEPRINT.md`, `MVP2.md` §6.4 |
| D-06 | Publicación | (Sin pregunta) | **Commit y push en `dev`** de backend y frontend. | Commits `8bd6fb8` y `056c5cf` |
| D-07 | Evaluación con la rúbrica | Faltantes frente a la rúbrica y oferta de completar la documentación. | Se dejó en espera: el equipo priorizó corregir la experiencia de voz (D-08). | §5.2, etapa 5 |
| D-08 | Ajuste de la voz | Convertir el pedido del asistente global en dos prompts: especificar una **HU20** e implementarla. | **No es una HU nueva, es una corrección** al resultado entregado; crear un reporte de correcciones. | §2 (C-01) |
| D-09 | Organización | ¿Subir el reporte a `dev` o ejecutar ya el prompt de C-01? | Primero **documentar las preguntas y decisiones** y renombrar el documento a "reportes y discusión". | Este documento |
| D-10 | Precisión del asistente | Cómo lograr que el asistente "casi no falle": meta medible, desambiguación en lugar de "no te entendí", y mantener la interpretación local sin LLM. | Registrarlo como **corrección C-02** con el mismo formato que C-01. La opción de un servicio de NLU externo queda abierta para decidir si C-02 no alcanza la meta. | §3 (C-02) |
| D-11 | Confirmación por voz | Tratarlo como defecto de prioridad alta: reproducirlo con una prueba, interpretar "sí" y "no" según el estado, dar dos oportunidades y anunciar siempre el resultado. | Registrarlo como **corrección C-03** con el mismo formato. Se ejecuta antes que C-02. | §4 (C-03) |

### 5.2. Detalle por etapa

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
- **Resultado:** este documento, renombrado a `REPORTES-Y-DISCUSION.md`, con la sección de discusión (hoy §5).

#### Etapa 9 — Precisión del asistente de voz

- **Solicitud del equipo:** registrar como prompt de corrección, con el mismo formato, la siguiente observación: "No esta reconociendo lo que le digo correctamente y solo dice no te entendi, puedes hacer algo para que entienda mejor todas las instrucciones que le de? como leeme el ultimo gasto, el ultimo ingreso, todas las posibles solicitudes que haga un usuario, debes poder predecirlas para no caer tanto en esa respuesta de "no entendi" porque eso puede ser frustrante para el usuario asi que necesitamos que sea casi perfecto"
- **Lo que hizo la IA:**
  - Registró la **corrección C-02** (§3) con diagnóstico por capa (reconocimiento, normalización, interpretación, cobertura y respuesta de error) y un prompt de corrección.
  - Tradujo "casi perfecto" a una meta medible: corpus de ≥ 200 frases, ≥ 95 % de intención correcta y 0 guardados sin confirmación.
- **Lo que advirtió la IA:**
  - El código del asistente de C-01 no está en `origin/dev` de FrontFinanzas, por eso el prompt le pide al agente localizarlo y detenerse si no existe.
  - Se mantiene la interpretación local sin LLM, como exige `MVP2.md`. Si no alcanza la meta, un servicio de comprensión de lenguaje (por ejemplo Azure CLU) quedaría como corrección futura con aprobación del equipo (D-10).

#### Etapa 10 — La confirmación por voz no completa el registro

- **Solicitud del equipo:** registrar con el mismo formato la siguiente observación: "cuando me pide confirmar un gasto que le digo por voz, por mas que le digo que "si" a la confirmacion no continua a confirmarme que ya lo registró"
- **Lo que hizo la IA:**
  - Registró la **corrección C-03** (§4) como **defecto de prioridad alta**, por encima de C-02.
  - Hizo un diagnóstico con siete causas posibles: micrófono que no se reabre, "sí" no normalizado, interpretación sin contexto, palabras de una sílaba, error de guardado sin manejar, locución final cortada y eco.
  - Escribió un prompt que obliga a reproducir el defecto con una prueba antes de corregirlo.
- **Lo que advirtió la IA:**
  - El síntoma tiene varias causas posibles y sin el código de C-01 no se puede afirmar cuál es. Por eso el prompt pide demostrarla con una prueba que falle.
  - Se mantiene la regla de no guardar sin confirmación explícita (D-11).

### 5.3. Decisiones que tomó la IA sin consulta previa (para validar)

| Decisión | Motivo | Riesgo / cómo revertir |
|---|---|---|
| Agregar `microsoft-cognitiveservices-speech-sdk` al frontend | Es el SDK obligatorio definido en `MVP2.md` §3; sin él no hay voz. | Ninguno; ya estaba aprobado en la especificación. |
| Cargar el SDK desde su bundle oficial para navegador | La entrada principal del paquete arrastra módulos de Node (`https`, `url`) y el build fallaba. | Si el SDK cambia la ruta del bundle, ajustar `azure-speech-engine.ts` y `angular.json`. |
| Asociar el token de voz a la cuenta activa | Evita reutilizar el token de otra sesión en el mismo navegador. | Ninguno funcional; es una medida de seguridad adicional. |
| Verificar el frontend con Node 24 vía `npx` | El CLI de Angular 22 no corre con Node 22.19.0. | El equipo debe actualizar Node para usar `npm run lint/test/build` directamente. |
| Instalar `uv` con `pip --user` y crear `backend/.venv` | Necesario para correr ruff, mypy y pytest (D-03). | `.venv` está ignorado por git. |
