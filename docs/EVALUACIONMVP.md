# Evaluación: Resultados del MVP y la calidad de las respuestas de IA — Informe de resultados y mejoras aplicadas

## 1. Portada

| Campo | Valor |
|---|---|
| Proyecto | App de finanzas personales |
| Componentes revisados | BackFinanzas y FrontFinanzas |
| Tipo de evaluación | Revisión documental y resultados del MVP |

## 2. Control documental y alcance

Se revisaron los dos repositorios adjuntos, documentos del directorio `docs`, el Blueprint, el prompt de evaluación abierto y el Backlog en taiga. Se consultaron código, pruebas, manifiestos y workflow de CI.

**Premisa de trabajo:** El informe evalúa el producto y los artefactos.

## 3. Resumen ejecutivo

Los repositorios contienen una aplicación de finanzas personales con backend FastAPI y frontend Angular offline-first. La arquitectura, el contrato de sincronización y varias reglas de negocio están implementados en código. Hay pruebas unitarias, de integración, de seguridad y 28 escenarios BDD en seis archivos `.feature`. El plan del backend registra las fases como terminadas y reporta 319 pruebas y 98 % de cobertura.

## 4. Contexto y descripción del MVP

El producto busca registrar ingresos y gastos, clasificarlos, permitir trabajo sin conexión y sincronizar datos entre dispositivos. El `BLUEPRINT.md` define 15 historias, reglas de negocio y entregas. El backend está en `backend`; el cliente Angular está en el repositorio separado `FrontFinanzas`.

La especificación divide responsabilidades: el servidor conserva la copia persistente de los datos; el navegador trabaja con Dexie/IndexedDB y calcula consultas, resumen, gráficos y ocurrencias recurrentes. El objetivo y esta división aparecen en docs/TECHNICAL.md y en los README de ambos repositorios.

## 5. Objetivos de la evaluación

1. Comparar requerimientos del Blueprint con implementación y pruebas disponibles.
2. Separar funcionalidades especificadas, implementadas y efectivamente validadas.
3. Revisar la calidad documental de los prompts, decisiones y guías.
4. Identificar contradicciones, riesgos y mejoras verificables.
5. Determinar qué conclusiones sobre la IA y sus respuestas pueden sostenerse.

## 6. Alcance, metodología y criterios

Se priorizó evidencia directa en este orden: código y pruebas; manifiestos y CI; documentación técnica y de producto; export del tablero. El Blueprint se usa como especificación.

Se aplican estas categorías:

- **Implementada:** existe código que realiza la función.
- **Probada en fuente:** hay pruebas que verifican parte del comportamiento.
- **Parcial:** hay implementación con una brecha conocida o cobertura incompleta.
- **No verificable:** no hay evidencia suficiente de implementación, ejecución o resultado.
- **No identificada:** no se encontró la capacidad en los archivos revisados.

Los niveles de riesgo se asignan por impacto potencial, no por probabilidad.

## 7. Inventario y análisis de fuentes documentales

| Fuente | Aporta | Qué permite comprobar | Limitación |
|---|---|---|---|
| `BLUEPRINT.md` | Objetivos, HU01–HU15, criterios Gherkin, reglas y arquitectura objetivo | Qué se esperaba construir | No prueba implementación ni aceptación |
| docs/TECHNICAL.md | Arquitectura, stack, configuración, API y ejecución del backend | Diseño y comandos documentados | Se limita al backend; no sustituye la inspección del código |
| docs/TESTING.md | Pirámide, rutas de pruebas, cantidades declaradas y comandos | Estrategia y cobertura |  |
| docs/USER-MANUAL.md | Flujos esperados para usuario | Comportamiento previsto | El mismo manual advierte que las pantallas son guía funcional; no prueba cada flujo |
| docs/DECISIONS.md | Decisiones D-01–D-47, motivos y estado P/A | Contexto de diseño y riesgos reconocidos | Varias decisiones implementadas siguen marcadas como propuestas |
| docs/PLAN.md | Fases y estado de avance al 12-10-2026 | Avance declarado; reporta 319 |  |
| docs/PROMPTS.md | Prompts de producto, arquitectura, agentes, pruebas y frontend | Diseño de instrucciones y alcance esperado |  |
| `CLAUDE.md`, `AGENTS.md` | Reglas para Claude Code/agentes de desarrollo | Flujo de trabajo previsto |  |
| backend/pyproject.toml, `package.json` | Dependencias, scripts y configuración | Stack y comandos disponibles |  |
| backend/tests, pruebas frontend `*.spec.ts` | Casos automatizados presentes | Qué comportamientos se verificaron |  |
| .github/workflows/backend.yml | Servicios y gates de integración continua | Qué verifica el workflow cuando corre | |
| Backlog Taiga| Cinco épicas, 15 historias, fechas y estado del tablero | Existencia de historias y actividad de planificación |  |

## 8. Reconstrucción del proceso asistido por IA

La documentación describe un flujo de prompts encadenados:

1. **Prompt 1:** redactar el objetivo, glosario e historias.
2. **Prompt 2:** producir stack, arquitectura, datos, API y organización frontend.
3. **Prompt 3:** derivar instrucciones para agentes en `AGENTS.md` y `CLAUDE.md`.
4. **Prompt 4:** generar pruebas en cuatro niveles.
5. **Prompt maestro frontend:** construir el cliente por etapas, desde el núcleo offline hasta accesibilidad.

Esta secuencia está documentada en docs/PROMPTS.md, y el proyecto incluye un Blueprint, arquitectura, decisiones, plan y código. Eso respalda que existe una metodología prevista de desarrollo asistido.

## 9. Requerimientos y matriz de trazabilidad

| ID | Objetivo/requerimiento | Fuente y evidencia | Método de verificación | Resultado | Observaciones |
|---|---|---|---|---|---|
| R1 | Registrar y proteger cuentas | HU01–HU03; módulos `auth`; pruebas unitarias, integración y BDD | Ejecutar auth, revisar flujo browser-backend | Parcialmente cumplido | backend cubierto en código; proveedor de correo real ausente |
| R2 | Registrar y editar ingresos/gastos offline | HU04–HU06; `LocalStore`, repositorio movimientos y módulos backend | Pruebas offline, integración sync, recorrido e2e sin red | Parcialmente cumplido | hay lógica y pruebas de capas; no e2e en navegador |
| R3 | Eliminar con posibilidad de deshacer | HU07; borrado lógico en cliente y servidor, pruebas de dominio/API | Probar deshacer antes/después de sincronizar | Parcialmente cumplido | README reporta que falta gesto de deslizar |
| R4 | Categorías personalizadas y reasignación | HU08; `categories`, repositorios y pruebas unitarias/integración/BDD | Ejecutar categoría y verificar propagación a datos relacionados | Implementado y probado en fuente | catálogos escogidos y decisiones siguen con aprobaciones ambiguas |
| R5 | Recurrentes automáticos y confirmables | HU09; `RuleRepo.generateDue`, `occurrencesBetween`, backend sync | Probar calendario, reinicio y doble dispositivo | Implementado parcialmente y probado en fuente | generación ocurre al abrir/volver al cliente; no es tarea de servidor |
| R6 | Notas y etiquetas | HU10; reglas de movimientos y sync; pruebas | Probar ingreso, búsqueda y navegación por etiqueta | Parcialmente cumplido | README confirma que tocar etiqueta no navega al filtro |
| R7 | Historial local | HU11; rutas/repositorios y manual | Probar orden, agrupación, paginación y modo offline | Implementación presente; validación insuficiente | no hay pruebas de interfaz/historial identificadas |
| R8 | Búsqueda y filtros | HU12; filtros y `FiltersState` | Probar criterios combinados y accesibilidad | Parcialmente cumplido | falta navegación desde etiqueta; pruebas UI ausentes |
| R9 | Resumen mensual | HU13; `HomePage` y cálculos de dominio frontend | Comparar meses con datos de referencia | Implementación presente; no verificado funcionalmente | no se identificó spec frontend del resumen |
| R10 | Presupuestos y alertas | HU14; módulo backend y páginas/repositorio frontend | Probar umbrales, persistencia y meses anteriores | Backend probado en fuente; frontend no verificado | no se identificó prueba frontend dedicada |
| R11 | Gráficos de categorías/meses | HU15; ECharts y `charts.page` | Verificar datos, interacción, estado vacío y tabla accesible | Implementación presente; no verificado funcionalmente | no se identificó prueba del módulo |
| R12 | Sincronizar cambios por versión | sección 6.4; `PushChanges`, `PullChanges`, `SyncService`; unitarias, integración y BDD | Pruebas de idempotencia, paginación, rechazo e aislamiento | Implementado y probado en fuente | no se ejecutó en esta evaluación |
| R13 | Funcionamiento offline con outbox atómico | `LocalStore`, Dexie, `offline.spec.ts` | Ejecutar Vitest y recorrido con pérdida/retorno de red | Implementado y probado en fuente | verificado con API simulada en pruebas frontend, no contra backend real |
| R14 | Usabilidad responsive y accesible | Prompt frontend, layout, guía funcional | Auditoría WCAG AA con evidencia y dispositivos | No verificable | el prompt lo exige; no se encontró resultado de auditoría |
| R15 | Calidad de respuestas del agente IA | Prompt de evaluación y `docs/PROMPTS.md` | Revisar corpus de respuestas, prompts ejecutados y rúbrica ciega | No verificable | no hay corpus, modelo/versiones ni evaluaciones |

## 10. Evaluación de resultados funcionales

| Funcionalidad | Implementación observada | Pruebas disponibles | Evaluación |
|---|---|---|---|
| HU01 Registro | Endpoint, creación de categorías predeterminadas y páginas frontend | Unitarias, integración y escenario BDD | Implementado en backend; flujo completo de UI no verificado |
| HU02 Sesión | Login, cookie refresh, rotación, logout, limitador Redis; sesión local frontend | Unitarias, integración y BDD | Cobertura backend presente; sesión offline del navegador requiere ejecución real |
| HU03 Recuperación | Token de un uso, caducidad y revocación de sesiones; ARQ | Unitarias, integración y BDD | Lógica implementada; entrega del correo productivo no disponible |
| HU04–05 Gasto/ingreso | Validación de montos y categorías; persistencia local/outbox | Backend unitarias/integración; frontend money/rules/offline | Implementado en capas; no probado de punta a punta |
| HU06 Editar | Upsert local y de servidor; tipo de movimiento inmutable | Backend unitarias/integración | Implementación y pruebas fuente presentes |
| HU07 Eliminar/deshacer | Borrado lógico y restauración | Backend y pruebas offline | Parcial: falta gesto swipe según README; deshacer después de sync de ocurrencia recurrente es decisión D-39, marcada propuesta |
| HU08 Categorías | CRUD por sync, `name_key`, reasignación y categorías predeterminadas | Backend unitarias/integración/BDD; frontend rules | Implementado y cubierto en fuente |
| HU09 Recurrentes | Fechas/ocurrencias en frontend; servidor almacena y valida reglas | Frontend `offline.spec.ts`/`recurrence.spec.ts`; backend pruebas | Implementado por capas, no mediante worker backend |
| HU10 Notas/etiquetas | Validación y persistencia en sync; búsqueda local | Backend unitarias; frontend `rules.spec.ts` | Parcial; navegación al historial filtrado no implementada según README |
| HU11 Historial | Ruta de movimientos y datos locales | No se identificó prueba de vista | No verificado funcionalmente |
| HU12 Búsqueda/filtros | Estado y filtros locales | Prueba de reglas de filtros existe, no se identificó recorrido UI | Parcial y no validado end-to-end |
| HU13 Resumen | Cálculos en página del inicio y dominio local | Sin prueba frontend identificada | No verificado funcionalmente |
| HU14 Presupuesto | Casos de uso backend y vista local con presupuesto | Backend unitarias/integración | Lógica backend probada en fuente; avisos y gráficos frontend no comprobados |
| HU15 Gráficos | Página ECharts y configuración modular | Sin prueba frontend identificada | Implementación presente; exactitud y accesibilidad no verificadas |


## 11. Evaluación técnica

**Fortalezas observables**

- Capas de dominio, aplicación, infraestructura y API, con composición central en `backend/app/composition.py`.
- Sincronización push/pull incremental, cursor por versión y rechazos por cambio.
- Separación de persistencia local y servidor; `LocalStore` escribe datos y outbox en una transacción Dexie.
- Validaciones estrictas de esquemas, límites de lote, identificadores y montos enteros.
- Pruebas con PostgreSQL real según los fixtures, con migraciones Alembic.
- CI backend con Ruff, formato, mypy, pytest/cobertura mínima y chequeo del OpenAPI.

**Brechas técnicas y de documentación**

- `docs/TESTING.md` describe un registro duplicado como `409 Conflict`, mientras el código de integración prueba `422` y el manejador general de errores traduce errores de dominio a `422`.
- `docs/TESTING.md` incluye `/auth/me` en la lista de endpoints protegidos; el endpoint observado es `/me`.
- La prueba `test_restablecer_contrasena_revoca_todas_las_sesiones` en `tests/security/test_security.py` termina con `assert True` y no realiza el reset. Hay un flujo de integración con cobertura funcional equivalente en `tests/integration/auth/test_api.py`; aun así, esa prueba de seguridad individual no aporta verificación.
- El prompt frontend exige `npm run test:ci`, pero `package.json` no declara ese script. El cliente HTTP está implementado a mano; no se encontró dependencia `ng-openapi-gen` en ese manifiesto.
- Los documentos `TECHNICAL.md` y `USER-MANUAL.md` describen el alcance del repo backend y explicitan que el frontend vive fuera de ese repositorio. El frontend separado sí está entre los materiales de esta evaluación; no se interpreta esta separación como ausencia del cliente.
- `docs/PIPELINE-PLACEHOLDER.md` confirma que no hay pipeline de despliegue automático definido.

## 12. Evaluación de la calidad de respuestas de IA

| Dimensión | Resultado | Evidencia y límite |
|---|---|---|
| Exactitud factual | No evaluable para Claude | El código puede revisarse frente al Blueprint; no hay respuestas originales que atribuir y puntuar |
| Pertinencia | No evaluable como comportamiento del modelo | Los prompts tienen objetivos detallados; faltan entradas/salidas reales |
| Completitud | No evaluable como respuesta | Los repositorios contienen varias partes del alcance; no hay referencia de qué respuesta produjo cada parte |
| Coherencia | Parcialmente evaluable a nivel de artefactos | Hay divergencias de conteo, reglas y documentación, pero no se puede determinar si surgieron del modelo, edición humana o evolución |
| Seguimiento de instrucciones | Parcialmente evaluable como consistencia artefacto-especificación | Se identifican algunas brechas en el producto; no existe cadena prompt → respuesta → cambio aprobada |
| Seguridad y confiabilidad del modelo | No evaluable | No hay respuestas, ataques de prompt, registros ni política de uso operativo |
| Resultado del producto | Parcialmente evaluable | Código, pruebas fuente y decisiones permiten revisar implementación sin atribuir autoría |

### 12.1 Calificación de la asistencia de IA

Esta calificación es una **estimación cualitativa basada en los prompts, el código, las pruebas y las inconsistencias documentales**.

Se usa una escala de 1 a 5: **1** deficiente, **2** insuficiente, **3** aceptable con limitaciones, **4** bueno, **5** excelente. “No evaluable” se reserva para dimensiones que requieren evidencia que no está disponible.

| Dimensión evaluada | Calificación inferida | Confianza | Justificación |
|---|---:|---|---|
| Claridad y estructura de los prompts | **4/5** | Media | Los prompts definen roles, contexto, tareas, restricciones, formatos de salida y criterios de verificación. La secuencia por etapas ayuda a dividir el trabajo. |
| Definición de criterios comprobables | **4/5** | Media | Los prompts incluyen reglas de negocio, escenarios, ejemplos y condiciones para detenerse ante ambigüedades. Esto favorece resultados revisables. |
| Calidad y suficiencia del contexto suministrado | **3/5** | Media-baja | Hay referencias claras al Blueprint y a las decisiones, pero algunos prompts contienen placeholders —por ejemplo, `{{SALIDA_PROMPT_1}}`— en vez de entradas efectivamente versionadas. |
| Calidad inferida de los artefactos producidos con asistencia | **3/5** | Media-baja | Hay una implementación extensa, modular y con pruebas de backend y sincronización. A la vez, hay inconsistencias documentales, decisiones aún marcadas como propuestas y cobertura incompleta del frontend. |
| Calidad de la IA como agente de desarrollo | **3/5** | Baja | El resultado es compatible con asistencia útil para generar especificaciones, estructura y código.|
| Resultado del MVP con asistencia de IA | **3/5** | Media-baja | El backend y el núcleo de sincronización tienen evidencia sustancial en código y pruebas fuente. |

**Interpretación:** la valoración general propuesta es **3/5, aceptable con limitaciones**. Indica que los artefactos sugieren una asistencia útil para avanzar el MVP.

### 12.2 Análisis de los resultados atribuibles a la asistencia

Los prompts fueron útiles para convertir una idea general en entregables técnicos: historias con criterios de aceptación, arquitectura, reglas de sincronización, instrucciones operativas y planes de prueba. La organización en prompts encadenados y el uso de criterios verificables fueron fortalezas del proceso.

La evidencia del producto también muestra un resultado técnico considerable: existen módulos de autenticación y sincronización, persistencia PostgreSQL, almacenamiento local con Dexie, outbox transaccional, pruebas de dominio e integración y escenarios BDD. Estas características son consistentes con el alcance de los prompts.

## 13. Evaluación de los prompts e ingeniería de prompts

La documentación de prompts tiene varios elementos de buena especificación: rol, contexto, restricciones, contratos de salida, ejemplos, condiciones de parada y listas de autoverificación. El encadenamiento de especificación funcional, arquitectura, instrucciones operativas y pruebas facilita la trazabilidad prevista.

| Prompt/documento | Aspectos sólidos | Brechas observables |
|---|---|---|
| Prompt 1: historias | Define 15 HU, orden, Gherkin, fuera de alcance y regla para detenerse ante ambigüedad | Exige mínimo tres escenarios por historia; la salida debe auditarse contra ese requisito. No hay registro de ejecución o revisión |
| Prompt adicional MoSCoW/IA | Distingue apoyo de IA de IA como función del producto y separa esfuerzo | No se encontró su tabla de salida. Su puntuación potencial no evidencia uso real |
| Prompt 2: arquitectura | Define capas, datos, offline, contratos, trazabilidad y preguntas de parada | Alta densidad de decisiones obligatorias; necesita registrar aprobación de propuestas y evitar que supuestos se vuelvan contrato |
| Prompt 3: agentes | Reglas de trabajo y seguridad concretas; mantiene `CLAUDE.md` delgado vía `@AGENTS.md` | No hay historial de cumplimiento por sesión o evidencia de aprobación de planes |
| Prompt 4: pruebas | Pide aislamiento, fixtures, aserciones específicas, seguridad y BDD | Incluye una aspiración de “cero falsos positivos”, que no es garantía demostrable; existe una prueba de seguridad con `assert True` |
| Prompt maestro frontend | Especifica offline-first, accesibilidad, módulos y casos de aceptación | Solicita `test:ci`, ausente del package; pide cobertura de componentes/e2e no presente en las cinco specs encontradas |
| Prompt de esta evaluación | Requiere evidencia, incertidumbre, trazabilidad y no inventar | Asume que todo se generó con IA y pide evaluar calidad de respuestas sin exigir transcripciones; esa premisa no basta para atribución por cambio |

## 14. Resultados cuantitativos y cualitativos

- Historias Scrum en el export: **15**, dentro de **5 épicas**.
- Escenarios BDD encontrados: **28** en seis archivos `.feature`.
- Archivos frontend `*.spec.ts` encontrados: **5**.
- Suite backend declarada: **268** en `docs/PLAN.md`; **319** en `docs/TESTING.md`.
- Cobertura backend declarada: **98 %** en `docs/PLAN.md`; gate de CI: mínimo **90 %**.

## 15. Incidencias, errores y limitaciones identificados

1. **Correo de recuperación no productivo.** El adaptador `LogEmailSender` escribe el enlace en logs. El worker falla al iniciar con `COOKIE_SECURE=true` mientras falte proveedor real. Se encuentra en `backend/app/modules/auth/infrastructure/mailer.py` y `backend/app/worker.py`.
3. **Inconsistencias documentales.** Conteos 319 y errores `409`/`422`; referencia `/auth/me` frente a `/me`.
4. **Alcance funcional incompleto.** README frontend identifica el gesto swipe y navegación al filtro desde etiqueta como pendientes.
5. **Especificación y decisiones abiertas.** `docs/DECISIONS.md` conserva decisiones `P` (propuestas) que aparecen reflejadas en código:
   - D-14 tolera una fecha hasta un día UTC futuro aunque HU04 prohíbe fechas futuras.
   - D-30 implementa una lista acotada de monedas, no la lista ISO 4217 completa solicitada.
   - D-37 elige catálogos de iconos/colores sin confirmación documentada.
   - D-39 limita el deshacer de una ocurrencia recurrente si el borrado ya se sincronizó.
   - D-43, D-44, D-45, D-46 y D-47 también aparecen como propuestas pese a describir comportamiento implantado.
7. **Pruebas de UI y accesibilidad insuficientes.** No se identificaron pruebas e2e ni pruebas de componentes para resumen, historial, presupuestos o gráficos.
8. **Despliegue no definido.** El placeholder del pipeline confirma que plataforma, ambientes, rollback, observabilidad y despliegue siguen pendientes.
9. **Riesgo de fixtures.** El fixture backend elimina y recrea `finanzas_test` en PostgreSQL local. Ejecutarlo apuntando a datos reales puede destruirlos.

## 16. Informe de mejoras aplicadas

La tabla registra cambios visibles en código/documentación y pruebas asociadas.

| ID | Problema/oportunidad | Cambio presente | Evidencia de aplicación | Resultado observado / estado |
|---|---|---|---|---|
| M-01 | Escrituras offline deben sobrevivir a desconexiones | Persistencia local y outbox en una transacción | `local-store.ts`, `offline.spec.ts` | Implementada; test presente, corrida|
| M-02 | Un cambio inválido no debe abortar lote sync | Savepoint por cambio y lista `rejected` | `push.py`, `test_push_pull.py`, BDD sync | Implementada y cubierta en fuente |
| M-03 | Versionado debe quedar bajo control servidor | Secuencia/triggers SQL | `migrations/versions/0001_esquema_inicial.py`, `test_schema.py` | Implementada y cubierta en fuente |
| M-04 | Reutilización de refresh token puede comprometer sesión | Rotación y revocación por familia | `auth` y `integration/auth/test_api.py` | Implementada|
| M-05 | Recurrentes pueden duplicarse entre dispositivos | UUID determinista y `generateDue` en cliente | `rule.repo.ts`, `recurrence.ts`, `offline.spec.ts` | Implementada; cubre lógica local, no recorrido multi-dispositivo real |
| M-06 | Correo de desarrollo podría exponer enlace en entorno seguro | Worker falla con cookie segura sin proveedor real | `backend/app/worker.py`, D-47 | Mitigación implementada; la funcionalidad de correo queda pendiente |
| M-07 | Prompts pretenden evaluaciones por escenarios | Se añadieron cuatro capas backend y pruebas offline frontend | Árbol de pruebas y `docs/TESTING.md` | La presencia se verifica; conteo/ejecución |
| M-08 | Swipe y navegación por etiqueta | No implementadas según notas del README frontend | `README.md` | Propuestas/pendientes, no mejoras aplicadas |

## 17. Análisis de brechas y riesgos

Criterio: **Alta** implica impacto considerable en seguridad, recuperación o fiabilidad; **Media** implica degradación funcional o ausencia de evidencia de validación; **Baja** es una mejora de experiencia no bloqueante. No se estima probabilidad.

| ID | Tipo | Situación y evidencia | Impacto potencial | Severidad | Prioridad / cierre verificable |
|---|---|---|---|---|---|
| G-01 | Operación/seguridad | Sin proveedor de correo; link se registra en logs y worker seguro no inicia | Recuperación inutilizable o exposición accidental en logs de desarrollo | Alta | P0: proveedor probado; logs no contienen token; flujo completo pasa |
| G-02 | Funcionalidad | Dos diferencias HU07/HU10 confirmadas en README | Menor consistencia con experiencia esperada | Media | P1: criterios y prueba de interfaz para swipe y apertura de filtro, o actualizar HU |
| G-03 | Especificación | Varias decisiones propuestas ya implementadas y D-14/D-30 difieren del Blueprint | Comportamiento sin aceptación inequívoca | Alta | P0: PO acepta o revierte cada desviación y actualiza fuente de verdad |
| G-04 | Integración | Verificación del frontend con simulacro, no con API real | Fallos de contrato, cookies, CORS o sincronización en uso combinado | Alta | P1: recorrido automatizado frontend-backend con PostgreSQL/Redis |

## 18. Plan de mejora continua

| Horizonte / ID | Acción | Responsable sugerido | Indicador y criterio de cierre | Evidencia requerida |
|---|---|---|---|---|
| Corto P0-1 | Elegir proveedor de correo e integrar sin registrar tokens en logs | Backend y seguridad | Recuperación completa probada; worker seguro arranca y correo llega | Test de integración y configuración sin secretos |
| Corto P0-2 | Resolver discrepancias 268/319 y corregir documentación 409/422, `/auth/me`/`/me` | QA y mantenedores docs | Conteo reproducible y documentación alineada al código | Salida `pytest --collect-only`, CI y cambios doc |
| Corto P0-3 | Reemplazar el test de seguridad `assert True` por aserciones reales o retirarlo | QA backend | Prueba falla si sesiones no se revocan | Test ejecutado que compruebe token/cookie anterior inválido |
| Corto P0-4 | Aprobar decisiones D-14, D-30, D-37, D-39 y otras `P` implementadas | Product Owner y líderes técnico/funcional | Cada decisión tiene estado aprobado/rechazado y fuente actualizada | Decisiones y Blueprint versionados |
| Mediano P1-1 | Crear prueba integrada browser/API para registro, sync, rechazo y refresh | QA frontend/backend | Recorrido pasa con servicios reales y modo offline/online | CI o reporte reproducible |
| Mediano P1-2 | Completar o redefinir swipe y navegación por etiquetas | Producto y frontend | Criterios aprobados y pruebas de componente/e2e | Casos de aceptación automatizados |
| Mediano P1-3 | Auditar accesibilidad en formularios, navegación y gráficos | UX/QA | Hallazgos críticos cerrados; teclado y etiquetas verificados | Informe de auditoría y regresión |
| Mediano P1-4 | Añadir tests frontend para historia, resumen, presupuestos y gráficos | Frontend/QA | Cálculos de referencia y navegación cubiertos | Specs con casos y resultado CI |
| Largo P2-1 | Definir despliegue, migraciones, backup, rollback y observabilidad | Plataforma/operaciones | Simulación de despliegue y rollback documentada | Runbook, workflow y evidencia de staging |
| Largo P2-2 | Establecer protocolo de evaluación de asistencia IA | Responsable QA/IA y PO | Corpus sintético, criterios, versionado y revisión humana aprobados | Corridas anonimizadas, resultados y decisiones |

## 19. Conclusiones generales

- **Alcanzado a nivel de implementación backend:** hay módulos, API, persistencia, migración, lógica de dominio y pruebas fuente para autenticación y datos sincronizables.
- **Parcialmente alcanzado:** experiencia offline, movimientos, categorías, recurrentes, filtros, resumen, presupuestos y gráficos existen en frontend.
- **No alcanzado como servicio productivo:** el correo real de recuperación no está integrado; tampoco hay despliegue definido.
- **Fortaleza:** buena descomposición por módulos, sincronización incremental, pruebas por capas y reconocimiento explícito de decisiones/riesgos.

## 20. Recomendaciones priorizadas

1. Cerrar el proveedor de correo y evitar filtración de enlaces en logs.
2. Unificar el inventario y ejecutar la suite desde un entorno reproducible; publicar salida y cobertura.
3. Añadir evidencia de accesibilidad y de las vistas frontend sin cobertura.

## 21. Referencias y trazabilidad documental

- Requerimientos: `BLUEPRINT.md`.
- Decisiones: `DECISIONS.md`.
- Arquitectura/configuración: `TECHNICAL.md`, backend/app/main.py, backend/app/composition.py.
- Pruebas y plan: `TESTING.md`, `PLAN.md`, backend/tests.
- Prompts: `PROMPTS.md`, `PromptEvaluacion_Mvp`.
- Cliente y sincronización: `README.md`, src/app/core/local-store.ts, src/app/core/sync.service.ts.
- Pipeline: `backend.yml`, `PIPELINE-PLACEHOLDER.md`.
- Prueba de auth con flujo completo: backend/tests/integration/auth/test_api.py.
- Prueba de seguridad con aserción vacía: backend/tests/security/test_security.py.
- Manual: `USER-MANUAL.md`.