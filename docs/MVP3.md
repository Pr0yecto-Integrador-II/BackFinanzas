# MVP 3: Ampliación con análisis de imágenes

Estado: **borrador para revisión del humano** (2026-11-23). Nada de este documento está aprobado hasta que su decisión aparezca como **A** en [AI-LOG.md](AI-LOG.md).

Fuentes de verdad: [BLUEPRINT.md](../BLUEPRINT.md) y [AGENTS.md](../AGENTS.md). Este plan sigue el mismo formato que [MVP2.md](MVP2.md). Si algo de aquí contradice esos documentos, mandan ellos y se pregunta.

## 1. Contexto y relación con el MVP 1 y el MVP 2

- **MVP 1:** núcleo offline-first (Dexie + `outbox`, sincronización `push`/`pull`, movimientos, categorías, recurrentes, presupuestos).
- **MVP 2:** voz. El backend emite un token temporal (`POST /speech/token`), el navegador dicta y lee en voz alta, y el dictado termina en un **borrador que el usuario confirma**.
- **MVP 3:** el usuario **fotografía** una compra, un recibo, un comprobante o una libreta, y la app propone uno o varios movimientos. Reutiliza el patrón del MVP 2: servicio externo detrás de un módulo del backend, interpretación en el dominio puro del navegador, confirmación antes de guardar.

El MVP 3 **no cambia** las reglas de negocio, el modelo de datos ni la sincronización, salvo la historia de adjuntos (HU26), que sí los toca y por eso queda bloqueada hasta resolver D3-04.

## 2. Cómo se usa la IA en este MVP y qué decide el humano

Este MVP tiene **dos usos distintos de IA**. Conviene no mezclarlos en el registro:

| Uso | Qué es | Dónde queda registrado |
|---|---|---|
| **IA como herramienta de desarrollo** | Claude Code (u otro agente) redacta historias, prompts, código y pruebas | [AI-LOG.md](AI-LOG.md): bitácora de sesiones |
| **IA dentro del producto** | Azure AI Vision lee la imagen (OCR, etiquetas, descripción). Es un servicio externo | Decisiones D3-01 a D3-03, D3-05 |

### Reparto de responsabilidades

| Tema | La IA hace | El humano decide |
|---|---|---|
| Alcance | Propone qué historias salen de las 7 ideas, con prioridad y esfuerzo | Qué entra, qué se pospone, el orden de las entregas |
| Servicio externo | Compara opciones y señala riesgos | Qué proveedor, región, costo y qué datos salen del servidor |
| Dependencias | Pide autorización y justifica | Autoriza o rechaza |
| Modelo de datos y sincronización | Describe el impacto y las alternativas | Aprueba cualquier cambio (`AGENTS.md`: «Cuándo detenerte y preguntar») |
| Código y pruebas | Escribe, ejecuta y reporta | Revisa el diff, confirma que lint, tipos, pruebas y build están en verde |
| Textos de la interfaz y mensajes de error | Redacta | Aprueba el tono y el texto exacto |
| Muestras reales (fotos de recibos, comprobantes, libretas) | No puede inventarlas | Las aporta, anonimizadas |
| Commit, push y merge | Solo si el humano lo pide | Siempre |

### Flujo humano-en-el-bucle de cada historia

1. **El humano** elige la historia y comparte el prompt (sección 6).
2. **La IA** entra en modo plan y propone archivos por capa. **El humano aprueba el plan** (C1).
3. Si aparece una decisión abierta, **la IA se detiene y pregunta** (C2/C3). **El humano responde** y la respuesta se anota en el registro.
4. **La IA implementa** de adentro hacia afuera y ejecuta los comandos de calidad.
5. **La IA entrega el reporte** con el formato de `AGENTS.md` más una entrada para [AI-LOG.md](AI-LOG.md).
6. **El humano revisa el diff, confirma y decide el commit** (C4–C6).

## 3. Objetivos

**General.** Reducir la fricción de registrar gastos cuando no hay un registro cómodo: sin recibo, con comprobante digital, con una libreta o con una factura de servicios.

**Específicos.**
1. Sugerir categoría desde la foto de una compra (idea 1, la de mayor valor).
2. Crear borradores de movimiento desde comprobantes de Nequi, Daviplata o Bancolombia (idea 3) y desde notas manuscritas (idea 2).
3. Proponer una regla recurrente desde una factura de servicios (idea 4).
4. Leer en voz alta lo detectado antes de guardar (idea 6, une MVP 2 y MVP 3).
5. Adjuntar el comprobante y mostrar miniatura (idea 5), y buscar recibos por descripción (idea 7), **sujetos a decisión**.

## 4. Decisiones abiertas (las toma el humano)

Cada una trae mi recomendación, pero **ninguna está aceptada**. Responde marcando A o R en [AI-LOG.md](AI-LOG.md) §4.

### D3-01 · Servicio de análisis de imágenes (hallazgo importante)

- **Contexto:** las 7 ideas parten de «Image Analysis 4.0». La documentación pública de Microsoft indica que Image Analysis 4.0 **está deprecado y se retira el 25 de septiembre de 2028**. Además, la descripción (*caption*) 4.0 solo existe en algunas regiones, y la versión 3.2 de *caption* sí está en todas.
- **Por qué importa:** el proyecto es académico y de corta vida, así que 2028 quizá no estorba; pero construir sobre un servicio que ya anuncia su retiro es una deuda que conviene aceptar a conciencia.
- **Opciones:**
  1. Azure AI Vision 4.0 tal cual (OCR *Read*, etiquetas, descripción, objetos). Menor cambio frente a la idea original.
  2. Solo el OCR *Read* de Azure AI Vision (o Document Intelligence para recibos) y **dejar fuera** etiquetas y descripción. Cubre HU22–HU24 y HU26, pero no la idea 1.
  3. Otro servicio con visión, como un modelo multimodal de lenguaje. Cubre la idea 1 con mejor español, pero el costo y la privacidad cambian.
- **Recomendación:** opción 1 para el MVP, con el servicio detrás de un **puerto** (`ImageAnalyzer`) para poder cambiarlo sin tocar dominio ni UI.
- **Lo que no sé y debe probarse (Fase 0):** qué idiomas devuelven etiquetas y descripción (probablemente inglés), qué regiones admiten *caption*, y qué tan bien lee letra manuscrita en español la versión 4.0 (la documentación confirma español manuscrito para *Read* en general, no específicamente para 4.0).

### D3-02 · El backend hace de intermediario

- **Decisión propuesta:** el navegador envía la imagen a `POST /vision/analyze` y el backend llama a Azure. La clave nunca sale del servidor.
- **Razón:** en el MVP 2 se usó un token temporal porque el SDK de voz lo permite. Para visión no lo he confirmado, y un intermediario además deja aplicar límites, tamaño máximo y no registrar la imagen.
- **Costo:** la imagen pasa por nuestro servidor. Es **un servicio externo nuevo**, así que según `AGENTS.md` requiere tu autorización.

### D3-03 · Las imágenes no se guardan en el servidor para analizarlas

- **Decisión propuesta:** el backend procesa la imagen en memoria, devuelve el resultado y la descarta. Nunca se registra en logs ni su contenido ni el texto leído.
- **Razón:** un recibo contiene datos sensibles (comercio, montos, a veces nombres y números de cuenta). `AGENTS.md` prohíbe datos sensibles en logs.
- **Pendiente:** confirmar en las condiciones de Azure cuánto retiene del lado del proveedor y avisar al usuario con un texto de consentimiento (que redactaré, tú apruebas).

### D3-04 · Dónde vive la foto adjunta (HU26)

Es el punto que **cambia el modelo de datos y el protocolo de sincronización**, así que me detengo aquí.

| Opción | Qué implica | Problema |
|---|---|---|
| A. Solo en el navegador (Blob en Dexie) | Una nueva `version(n)` de Dexie, sin servidor | Se pierde en otro dispositivo, y el cierre de sesión borra los datos locales (HU02) |
| B. En el servidor | Almacenamiento de objetos, tabla `attachments`, migración nueva, cambios en `push`/`pull`, subida de archivos sin conexión | Es una historia grande y un servicio más |
| C. No guardar la foto | Se guarda solo el movimiento | No cumple la idea 5 |

- **Recomendación:** C para las entregas R1 y R2 y **decidir A o B** cuando llegue R3, con datos de uso reales.

### D3-05 · La interpretación del texto es determinista

- **Decisión propuesta:** la IA externa solo **lee** la imagen. Convertir texto en monto, fecha, tipo y categoría lo hace código del dominio con reglas y pruebas, igual que el parser de dictado del MVP 2.
- **Razón:** un monto mal interpretado es un error financiero; el código determinista se prueba con valores exactos. Ejemplo: «15.000» → `amount_minor = 1_500_000` (enteros, nunca `float`).
- **Costo:** las reglas por entidad (Nequi, Daviplata, Bancolombia) son frágiles si el banco cambia su pantalla.

### D3-06 · Nada se guarda sin confirmación

- **Decisión propuesta:** el resultado es siempre un **borrador** editable. Las notas manuscritas generan varios borradores que se confirman uno por uno.
- **Razón:** mismo criterio de MVP 2 («guardado automático sin confirmación» fuera de alcance), y el OCR se equivoca.

### D3-07 · Sin conexión se degrada a registro manual

- **Decisión propuesta:** el análisis requiere conexión. Sin ella, la app avisa y deja el registro manual intacto (como en voz). **No** se encolan fotos para analizarlas después.
- **Razón:** encolar imágenes obliga a guardarlas (ver D3-04).

### D3-08 · Cuota de análisis por usuario

- **Propuesta:** límite por hora en Redis, con el `RateLimiter` ya existente, como en voz (30/hora). **El número lo pones tú**, porque depende del costo que quieras asumir y del plan de Azure.

### D3-09 · La búsqueda por embeddings queda fuera del MVP 3

- **Propuesta:** idea 7 → `Won't` en este MVP.
- **Razón:** exige guardar un vector por foto (por ejemplo, con `pgvector`, que es una dependencia y una extensión nuevas), consultas en el servidor que rompen el principio de que la búsqueda es local (HU12), y depende de que las fotos se guarden (D3-04 opción B).

### D3-10 · Muestras reales

- **Lo que necesito de ti:** 20 a 30 imágenes **anonimizadas**: capturas de Nequi, Daviplata y Bancolombia (con «Enviaste» y «Recibiste»), fotos de libretas manuscritas, una factura de servicios y fotos de compras. Sin ellas, las reglas de la idea 3 y 2 serían adivinanzas.

## 5. Historias propuestas

Numeración continúa desde HU19 (MVP 2). Clasificación, MoSCoW y esfuerzo son **propuestas de la IA**; el humano las valida. Escala igual que [BLUEPRINT.md](../BLUEPRINT.md) (Puntos IA 0–5, esfuerzo 1–10).

### 5.1. Mapa

| Módulo | HU | Historia | Idea | Fase | Depende de |
|---|---|---|---|---|---|
| 7. Imágenes | HU20 | Autorización y análisis seguro de imágenes | – | MVP3-R1 | HU02, D3-01 a D3-03 |
| 7. Imágenes | HU21 | Foto de la compra → categoría sugerida ⭐ | 1 | MVP3-R1 | HU04, HU08, HU20 |
| 7. Imágenes | HU25 | Escuchar lo detectado antes de guardar | 6 | MVP3-R1 | HU18, HU21 |
| 7. Imágenes | HU22 | Comprobante de Nequi, Daviplata o Bancolombia → borrador | 3 | MVP3-R2 | HU04, HU05, HU20, D3-10 |
| 7. Imágenes | HU23 | Notas manuscritas → varios borradores | 2 | MVP3-R2 | HU04, HU20, D3-10 |
| 7. Imágenes | HU24 | Factura de servicios → regla recurrente propuesta | 4 | MVP3-R2 | HU09, HU20 |
| 7. Imágenes | HU26 | Recibo adjunto como comprobante con miniatura | 5 | MVP3-R3 | **D3-04** |
| 7. Imágenes | HU27 | Buscar recibos por descripción | 7 | Aplazada | **D3-09** |

### 5.2. Clasificación y estimación

| HU | Puntos IA | Clasificación | MoSCoW | Esfuerzo | Justificación |
|---|---:|---|---|---:|---|
| HU20 | 3 | Híbrida | Must | 5 | Mismo patrón que HU16, pero maneja imágenes: tamaño y tipo máximos, tiempos, privacidad y dependencia externa nueva |
| HU21 | 3 | Híbrida | Must | 6 | La tabla de mapeo es simple; la calidad depende de lo que devuelva el servicio, y las categorías son personalizables (HU08) |
| HU25 | 4 | Principalmente con IA | Should | 3 | Reutiliza el sintetizador de HU18 con un formateador puro |
| HU22 | 2 | Híbrida | Should | 7 | Reglas por entidad, frágiles; requiere muestras reales |
| HU23 | 2 | Híbrida | Could | 8 | La precisión del OCR manuscrito es incierta; varios borradores y confirmación uno por uno |
| HU24 | 3 | Híbrida | Could | 6 | Debe encajar con las reglas de HU09; la fecha límite no es la fecha de inicio |
| HU26 | 2 | Híbrida | Could | 9 | Cambia modelo de datos y sincronización si se elige B |
| HU27 | 1 | Tradicional | Won't | 9 | Vectores, extensión nueva y búsqueda en servidor |

### 5.3. Reglas comunes a todas las historias

1. **Dinero:** entero en centavos (`amount_minor`). Se interpreta el formato colombiano: «45.900» son 45 900 pesos = `4_590_000`. Nunca `float`.
2. **Borrador, no movimiento:** ningún análisis crea un movimiento por sí solo (D3-06).
3. **Una sola ruta de guardado:** el borrador confirmado pasa por la misma validación de HU04/HU05 y se guarda en Dexie y en el `outbox` en **la misma transacción**.
4. **Fecha:** se valida con `Clock`; una fecha leída del recibo que sea futura se rechaza o se ajusta con aviso, nunca se guarda tal cual.
5. **Tipo:** el tipo del movimiento debe coincidir con el de la categoría (HU04/HU05).
6. **Privacidad:** el backend no registra imagen ni texto leído; el frontend no los envía a ningún otro servicio.
7. **Degradación:** sin conexión, sin permiso de cámara o con el servicio caído, el registro manual sigue funcionando.
8. **Accesibilidad:** resultados y errores en regiones `aria-live`; todo flujo con foto tiene alternativa manual.

### 5.4. Detalle por historia

El detalle completo (reglas numeradas, escenarios Gherkin y casos límite) lo genera el **Prompt P1** de la sección 6 y se pega aquí en cuanto el humano lo revise. Mientras tanto, los resúmenes:

- **HU20.** `POST /vision/analyze` recibe una imagen (JPEG, PNG; tamaño máximo a definir), exige sesión, aplica la cuota de D3-08 y devuelve `{ocr_lines, tags, caption, objects}` normalizado. 401 sin sesión, 413 si es muy grande, 415 si el tipo no es admitido, 429 sin cuota y 503 si el servicio falla o no está configurado. No guarda nada.
- **HU21.** Foto → etiquetas y descripción → tabla de mapeo (`food` → Alimentación, `car`/`fuel` → Transporte, `medicine` → Salud, entre otras) → **categoría sugerida** entre las del usuario, resuelta por `name_key`. Si la categoría no existe o no hay coincidencia, no se sugiere nada. El usuario siempre puede cambiarla.
- **HU25.** «Recibo de Éxito, total cuarenta y cinco mil novecientos pesos». Formateador puro en el dominio; el sintetizador del MVP 2 lo reproduce. El botón es opcional, nunca automático.
- **HU22.** Texto del comprobante → reglas por entidad. «Enviaste» → gasto; «Recibiste» → ingreso. Si no se reconoce la entidad o el texto es ambiguo, borrador vacío con aviso.
- **HU23.** Líneas de la libreta («almuerzo 15.000», «bus 2.950», «arriendo 900.000») → un borrador por línea con monto válido; las líneas sin monto se muestran y se descartan.
- **HU24.** Valor y fecha límite de una factura → regla propuesta, que el usuario edita y confirma en el módulo de recurrentes.
- **HU26.** Bloqueada por D3-04.
- **HU27.** Aplazada.

## 6. Prompts

> **Uso.** Cada prompt es autocontenido para un agente abierto en la raíz del repositorio. Una historia por sesión. El backend vive en BackFinanzas; las tareas de Angular/Dexie viven en **FrontFinanzas**. Conforme a `CLAUDE.md`, cada sesión **empieza en modo plan y espera aprobación**.
>
> **Orden:** Fase 0 → P1 → HU20 → HU21 → HU25 → (R2) HU22 → HU23 → HU24 → (R3, tras D3-04) HU26.
>
> **Cada prompt termina con el mismo contrato de salida**, que incluye una entrada para [AI-LOG.md](AI-LOG.md). Así el registro del uso de IA se alimenta solo.

### 6.0. Buenas prácticas aplicadas (heredadas de [PROMPTS.md](PROMPTS.md))

Etiquetas XML consistentes, rol único, documentos arriba y tarea al final, razón entre paréntesis en cada restricción, condiciones de parada que obligan a preguntar, criterios de verificación y ejemplos. No se repiten aquí las fuentes: están en `PROMPTS.md` §1.

### 6.1. Bloque común de salida (se pega al final de cada prompt)

```xml
<output_format>
1. Primero, en modo plan: archivos a crear o modificar por capa, decisiones abiertas que necesito del humano y riesgos. Espera aprobación antes de escribir código.
2. Al terminar, el reporte de `AGENTS.md` (Historia, Cambios, Pruebas, Criterios de aceptación → prueba, Comandos ejecutados, Pendientes).
3. Una entrada para `docs/AI-LOG.md` con estas columnas: Fecha | Herramienta y modelo | Qué pidió el humano | Qué produjo la IA | Qué debe revisar el humano | Resultado.
4. Una lista «Decisiones que tomé por mi cuenta» (si hubo alguna) para que el humano las acepte o las rechace. Si no hubo, escribe «Ninguna».
</output_format>

<stop_conditions>
Detente y pregunta si: una decisión D3-xx de la que depende esta historia sigue en estado P; necesitas una dependencia nueva; la solución cambia el modelo de datos, el protocolo de sincronización o una regla del Blueprint; o una prueba existente falla por algo que no tocaste.
</stop_conditions>
```

### 6.2. Fase 0: spike de viabilidad (el humano aporta las muestras)

```xml
<role>
Eres un ingeniero de datos que evalúa servicios de visión con rigor: mides antes de afirmar.
</role>

<context>
El MVP 3 de una app de gastos personales en COP depende de que un servicio de visión lea recibos, comprobantes y letra manuscrita en español, y devuelva etiquetas útiles para clasificar compras. Hay decisiones abiertas (D3-01, D3-03) que dependen de estos resultados. Esto es un spike: no se toca el código de la aplicación.
</context>

<documents>
- `docs/MVP3.md` §4 (D3-01, D3-03, D3-10).
- La carpeta de muestras anonimizadas que indique el humano.
</documents>

<task>
Escribe un script aislado, fuera de `backend/app` (por ejemplo en el directorio temporal), que envíe cada muestra al servicio y produzca una tabla: tipo de muestra, líneas OCR leídas, etiquetas, descripción, y si el monto y la fecha se leyeron correctamente (el humano los marca). Termina con un informe de 1 página: qué funciona, qué no, idiomas devueltos, región usada, latencia, y una recomendación sobre D3-01.
</task>

<constraints>
- No agregues dependencias al proyecto (el script usa lo ya instalado o `curl`). Una dependencia nueva requiere autorización.
- La clave se lee de una variable de entorno, jamás se escribe en archivos ni en el informe (secretos).
- No envíes muestras que el humano no haya marcado como anonimizadas (datos sensibles).
- No afirmes capacidades que no hayas medido: si algo no se probó, di «no probado».
</constraints>

<verification>
- [ ] Cada muestra aparece en la tabla.
- [ ] El informe distingue lo medido de lo supuesto.
- [ ] Ninguna clave ni imagen quedó dentro del repositorio.
</verification>
```
Agrega el bloque de §6.1.

### 6.3. P1: generar el detalle de las historias

```xml
<role>
Eres un analista de producto senior en finanzas personales, con experiencia en historias Connextra, reglas verificables y escenarios Gherkin. Escribes en español claro y preciso.
</role>

<context>
El MVP 3 añade análisis de imágenes a una PWA de gastos personales offline-first. Las historias HU20–HU27 ya tienen resumen, prioridad y esfuerzo propuestos. Falta el detalle para que un agente de código implemente cada una sin adivinar.
</context>

<documents>
- `docs/MVP3.md` completo (§4 decisiones y §5 historias).
- `docs/MVP2.md` solo la sección `#### HU17` como modelo de formato.
- `BLUEPRINT.md` solo `#### HU04` y `#### HU05`.
- `AGENTS.md`.
</documents>

<task>
Redacta el detalle de HU20, HU21, HU22, HU23, HU24 y HU25. Para HU26 y HU27 escribe solo «Bloqueada: ver D3-04» y «Aplazada: ver D3-09».
</task>

<instructions>
Cada historia, en este orden: encabezado `#### HUxx. Título`; frase Como / quiero / para en cita; contexto; reglas numeradas (tablas para campos) indicando si requiere conexión; criterios Gherkin con valores exactos (montos en centavos, fechas, textos de mensajes); casos límite; fuera de alcance; tareas técnicas por capa (Backend, Frontend, Contrato y calidad).
Mínimo 4 escenarios Gherkin por historia: camino feliz, ambigüedad o error de lectura, fallo de permisos o servicio, y sin conexión.
Respeta las reglas comunes de `MVP3.md` §5.3 y las decisiones D3-05 a D3-07.
</instructions>

<constraints>
- Si una decisión D3-xx de la que depende una historia está en estado P, **no la resuelvas**: escribe la historia con la suposición explícita y márcala «Supuesto, pendiente de decisión».
- No inventes reglas fuera de lo pedido: lo no pedido va en «Fuera de alcance» (evita construir de más).
- Ningún escenario usa «un monto» o «un mensaje»: usa números y textos exactos.
- Ejemplos de comprobantes de Nequi, Daviplata o Bancolombia: usa texto inventado y marca que debe sustituirse por muestras reales (D3-10); no copies formatos que no hayas visto.
</constraints>

<verification>
- [ ] Cada historia tiene ≥ 4 escenarios y casos límite.
- [ ] Ningún escenario guarda un movimiento sin confirmación.
- [ ] Todos los montos son enteros en centavos.
</verification>
```
Agrega el bloque de §6.1.

### 6.4. HU20: backend, módulo `vision`

```xml
<role>
Eres un ingeniero backend senior en Python 3.12, FastAPI, Pydantic v2, Redis y arquitectura hexagonal. Escribes código tipado (`mypy --strict`), probado y seguro por defecto. Sigues `AGENTS.md` al pie de la letra.
</role>

<context>
Repositorio BackFinanzas. Módulos existentes: auth, categories, transactions, recurring, budgets, sync, speech. El MVP 3 añade análisis de imágenes. HU20 es habilitadora: HU21–HU25 dependen de su contrato.
Piezas que DEBES reutilizar: `Clock`, el `RateLimiter` de auth (como hizo `speech`), la dependencia que resuelve el usuario del JWT, `Settings`, `composition.py`, `main.py`, el manejador de errores de `app/shared/errors.py` y `scripts/export_openapi.py`. Usa el módulo `speech` como modelo de estructura.
</context>

<documents>
- `docs/MVP3.md` §4 (D3-01, D3-02, D3-03, D3-08) y la sección HU20 una vez generada por P1.
- `docs/MVP2.md` §6.2–6.4 (cómo se hizo `speech`).
- `AGENTS.md`.
</documents>

<task>
Implementa `POST /vision/analyze`: recibe una imagen, exige sesión, aplica la cuota por usuario, llama al servicio de visión mediante un puerto y devuelve `{ocr_lines, tags, caption, objects}` normalizado. No persiste nada.
</task>

<instructions>
Dentro hacia fuera, con pruebas junto al código:
1. Configuración opcional (`app/config.py`, `.env.example` con valores vacíos): clave (`SecretStr`), endpoint/región, timeout, tamaño máximo de imagen, cuota por hora.
2. Dominio: dataclass inmutable `ImageAnalysis`; errores propios (`VisionUnavailableError` 503, `VisionRateLimitError` 429, `ImageTooLargeError` 413, `UnsupportedImageError` 415). Sin imports de FastAPI, Pydantic ni httpx.
3. Aplicación: puerto `ImageAnalyzer(Protocol)` y caso de uso `AnalyzeImage.execute(user_id, image: bytes, content_type: str)`. Valida tipo y tamaño **antes** de gastar cuota o llamar al servicio; la cuota cuenta cada intento, también los que terminan en 503 (como en `speech`).
4. Infraestructura: adaptador del servicio elegido en D3-01. Traduce credenciales ausentes, timeout, error de red y status distinto de 200 a `VisionUnavailableError`. Valida el tipo real por los primeros bytes, no solo por la cabecera.
5. API: `multipart/form-data` con un único archivo; `user_id` solo del JWT; `Cache-Control: no-store`; errores `{code, message}` en español.
6. Composición, registro del router y `openapi.json` regenerado.
</instructions>

<constraints>
- **Detente y pide autorización** si necesitas una dependencia nueva (por ejemplo, `python-multipart` para subir archivos) o si D3-01/D3-02/D3-03 siguen en P (servicio externo nuevo).
- Nunca registres en logs la imagen, el texto leído, la clave ni el nombre del archivo (datos sensibles).
- La imagen se procesa en memoria y se descarta; no hay tablas, migraciones ni almacenamiento (D3-03).
- Esquemas con `extra="forbid"` y límites; cualquier campo extra → 422.
- Sin `datetime.now()` en dominio ni aplicación.
</constraints>

<verification>
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` en verde.
- [ ] Pruebas para 200, 401, 413, 415, 422, 429 y 503, y para «el servicio caído consume cuota».
- [ ] Una prueba de seguridad comprueba que clave, imagen y texto leído no aparecen en los logs.
- [ ] `scripts/export_openapi.py --check` en verde.
</verification>
```
Agrega el bloque de §6.1.

### 6.5. HU21 y siguientes: frontend (FrontFinanzas)

Plantilla base. Se sustituyen los campos entre `{{ }}` con la tabla de §6.6.

```xml
<role>
Eres un ingeniero frontend senior en Angular (standalone, `OnPush`, signals, `inject()`), Dexie y diseño de dominio puro. Escribes código tipado y probado, accesible (WCAG AA) y sigues `AGENTS.md`.
</role>

<context>
Repositorio FrontFinanzas. El MVP 3 añade análisis de imágenes. El cliente de la API se regenera con `ng-openapi-gen` desde `backend/openapi.json` (HU20 ya está hecha). Reutiliza el patrón del dictado del MVP 2: adaptador del servicio, parser puro en el dominio, borrador editable, y guardado en Dexie + `outbox` en una sola transacción.
</context>

<documents>
- `docs/MVP3.md` §4, §5.3 y la sección {{HU}} generada por P1.
- `docs/MVP2.md` §4.3 HU17 y §6.6 (cómo quedó el dictado).
- `AGENTS.md`.
</documents>

<task>
Implementa {{HU}}: {{TAREA}}
</task>

<instructions>
Dominio → repositorio → página y componentes:
1. **Dominio puro** (sin Angular ni Dexie ni `Date` del sistema): {{DOMINIO}}. Montos en `amount_minor` entero; formato colombiano «45.900». Fechas con `Clock` inyectado.
2. **Adaptador**: el componente nunca usa `HttpClient`; todo pasa por un repositorio sobre el cliente generado.
3. **UI**: el resultado es un borrador editable; cámara o archivo; estados de carga, error y sin conexión en regiones `aria-live`; alternativa manual siempre disponible.
4. **Guardado**: el borrador confirmado pasa por la misma validación y servicio de HU04/HU05.
</instructions>

<constraints>
- Ningún movimiento se guarda sin confirmación (D3-06).
- Sin `innerHTML` con texto leído de la imagen ni `bypassSecurityTrust*` (el texto de un recibo es entrada no confiable).
- No se envía la imagen a ningún servicio distinto del backend propio.
- Sin conexión: mensaje claro y registro manual intacto (D3-07); no se encolan fotos.
- Sin dependencias nuevas sin autorización.
- {{RESTRICCION}}
</constraints>

<verification>
- [ ] `npm run lint && npm run test:ci && npm run build` en verde.
- [ ] Cada criterio Gherkin de {{HU}} tiene una prueba nombrada.
- [ ] Pruebas del dominio con montos exactos (por ejemplo, «15.000» → `1_500_000`).
</verification>
```
Agrega el bloque de §6.1.

### 6.6. Parámetros por historia

| HU | `{{TAREA}}` | `{{DOMINIO}}` | `{{RESTRICCION}}` |
|---|---|---|---|
| HU21 | Fotografiar una compra y obtener una categoría sugerida | Tabla de mapeo etiqueta → clave de categoría por defecto; resolución a la categoría del usuario por `name_key`; elección de la mejor coincidencia | Si el usuario no tiene la categoría sugerida, no se inventa ni se crea una (HU08) |
| HU25 | Escuchar en voz alta lo detectado antes de guardar | Formateador de «Recibo de {comercio}, total {monto en letras} pesos» a partir del borrador | Reutiliza el sintetizador de HU18; la lectura nunca es automática |
| HU22 | Crear un borrador desde un comprobante de Nequi, Daviplata o Bancolombia | Reglas por entidad: «Enviaste» → gasto, «Recibiste» → ingreso; extracción de monto, fecha y destinatario | **Usa las muestras reales de D3-10**; si falta alguna entidad, déjala fuera y repórtalo |
| HU23 | Convertir una libreta manuscrita en varios borradores | Separación por líneas y extracción de «concepto + monto» | Las líneas sin monto válido se muestran como descartadas; se confirma de a una |
| HU24 | Proponer una regla recurrente desde una factura de servicios | Extracción de valor y fecha límite; construcción de una regla compatible con HU09 | La fecha límite no es la fecha de inicio: el humano elige la frecuencia. No se crea la regla sin confirmación |
| HU26 | Adjuntar el recibo al movimiento con miniatura | Según D3-04 | **No empieces hasta que D3-04 esté aceptada** |

## 7. Cambios de reglas que propongo (no aplicados)

Conforme a `CLAUDE.md`, no los guardo solo en mi memoria. **Ninguno está aplicado**; los apruebas tú:

1. **`AGENTS.md`, «Cuándo detenerte y preguntar»:** añadir «El análisis de imágenes envía datos personales a un servicio externo» como motivo de parada.
2. **`AGENTS.md`, «Seguridad»:** añadir «Sin imágenes ni texto leído de ellas en logs».
3. **`BLUEPRINT.md`, §5 (stack):** si D3-01 se acepta, listar el servicio de visión.
4. **`AGENTS.md`, nueva sección «Registro de IA»:** cada sesión añade su entrada a `docs/AI-LOG.md`.

## 8. Plan de fases

| Fase | Contenido | Responsable | Puerta de salida |
|---|---|---|---|
| 0 | Muestras anonimizadas (D3-10), spike de viabilidad y decisión D3-01 | Humano aporta, IA mide | Informe del spike y D3-01 en A o R |
| 1 | Revisión de este documento, P1 y decisiones D3-02, D3-03, D3-05 a D3-08 | IA redacta, humano decide | Historias HU20–HU25 detalladas; decisiones en A |
| 2 | HU20 (backend) | IA implementa, humano revisa | Comandos de calidad en verde; OpenAPI actualizado |
| 3 | HU21, HU25 (frontend, R1) | Ídem | Idea 1 funcionando de extremo a extremo |
| 4 | HU22, HU23, HU24 (R2) | Ídem | Con muestras reales |
| 5 | D3-04 y, si se acepta, HU26 (R3) | Humano decide primero | Cambios de datos aprobados |

## 9. Registro de progreso

| Fase | Estado | Notas |
|---|---|---|
| 0 | ⬜ sin empezar | Espera muestras (D3-10) |
| 1 | 🟡 en revisión | Este documento es el borrador de la fase 1 |
| 2 | ✅ hecha en el código (2026-11-23) | HU20: módulo `vision` y `POST /vision/analyze` (imagen cruda, sin dependencias nuevas). 472 pruebas en verde en total; `domain`/`application` de `vision` al 100 %. **Probado contra Azure real (2026-11-23, región `northcentralus`) con una imagen sintética:** el OCR leyó «EXITO» y «TOTAL 45.900» y las etiquetas llegaron en inglés. **Hallazgo:** `caption` no existe en esa región (400), así que las características son configurables (`AZURE_VISION_FEATURES`, por defecto `read,tags`). Sin probar aún con recibos reales ni letra manuscrita |
| 3 | ✅ hecha en el código (2026-11-23) | HU21 y HU25 en `FrontFinanzas`: `receipt.ts`, `vision.service` y los botones «Foto de la compra» y «Escuchar lo detectado». Con Node 22.23.5: `npm run lint`, `npm test` (182 pruebas, 12 archivos) y `npm run build` en verde. Sin pruebas de componente de la página del formulario y **sin probar contra Azure real** |
| 4 | ⬜ | – |
| 5 | ⬜ | – |
