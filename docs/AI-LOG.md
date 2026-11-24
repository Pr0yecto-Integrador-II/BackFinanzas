# Registro de uso de IA y decisiones humanas

Este archivo es el registro vivo de **cómo se usa la IA en el proyecto** y **qué decide el humano**. Cubre todos los MVP. Se actualiza en cada sesión con IA, en el mismo commit que los cambios que esa sesión produjo.

## 1. Reglas del registro

1. **La IA propone; el humano decide.** Una propuesta de la IA nunca cuenta como decisión hasta que aparece aquí con `Decide: humano` y estado **A** (aceptada) o **R** (rechazada).
2. **La IA no inventa aprobaciones.** Si falta la respuesta del humano, el estado queda **P** (pendiente).
3. **Cada sesión deja una entrada** en la sección 3: qué se pidió, qué produjo la IA, qué revisó el humano y qué cambió.
4. **Lo que la IA no decide nunca:** dependencias nuevas o servicios externos, cambios al modelo de datos o al protocolo de sincronización, cambios a reglas de `BLUEPRINT.md`/`AGENTS.md`, qué datos del usuario salen del servidor, commits, push y merge.
5. **Cada decisión enlaza su razón.** Una decisión sin razón no se registra.

## 2. Puntos de control humanos

| # | Punto de control | Quién actúa | Evidencia que queda |
|---|---|---|---|
| C1 | Revisar la historia en el documento y aprobar el plan (`CLAUDE.md`: modo plan) | Humano aprueba | Estado del plan y entrada en la sección 3 |
| C2 | Resolver las decisiones abiertas de la historia | Humano decide | Fila en la sección 4 |
| C3 | Autorizar dependencias, servicios externos y cambios de contrato | Humano autoriza | Fila en la sección 4 |
| C4 | Revisar el diff y el reporte de la IA (formato de `AGENTS.md`) | Humano revisa | Campo «Qué revisó el humano» |
| C5 | Ejecutar o confirmar lint, tipos, pruebas y build | IA ejecuta, humano confirma | Resultado en el reporte |
| C6 | Commit, push y merge | Solo humano (o IA si lo pide) | Historial de Git |

## 3. Bitácora de sesiones con IA

| Fecha | Herramienta y modelo | Qué pidió el humano | Qué produjo la IA | Qué revisó o cambió el humano | Resultado |
|---|---|---|---|---|---|
| 2026-11-23 | Claude Code (Sonnet 5.5) | Plan del MVP 3 con análisis de imágenes (7 ideas), con decisiones y prompts, y registro del uso de IA | `docs/MVP3.md` (alcance, decisiones abiertas, prompts) y este archivo. Sin código. Contrastó las ideas con `AGENTS.md`, `BLUEPRINT.md`, `MVP2.md` y la documentación pública de Azure | **Pendiente:** el humano debe revisar `MVP3.md` y resolver las decisiones D3-01 a D3-10 | Borrador **P** |

> Las entradas nuevas se agregan arriba de la anterior o al final, pero siempre con fecha. Las sesiones de código añaden el reporte de `AGENTS.md` (historia, pruebas, comandos) en «Resultado».

## 4. Decisiones del humano

Las decisiones de producto y arquitectura del MVP 3 viven con su contexto en [MVP3.md §4](MVP3.md). Aquí queda el resumen de **quién decidió y cuándo**.

| ID | Decisión | Propone | Decide | Estado | Fecha |
|---|---|---|---|---|---|
| D3-01 | Servicio de análisis de imágenes (Image Analysis 4.0 está deprecado) | IA | humano | P | – |
| D3-02 | El backend hace de intermediario con el servicio de visión | IA | humano | P | – |
| D3-03 | Las imágenes no se guardan en el servidor para analizarlas | IA | humano | P | – |
| D3-04 | Foto adjunta al movimiento: dónde se guarda | IA | humano | P | – |
| D3-05 | La interpretación del texto es determinista, no un modelo de lenguaje | IA | humano | P | – |
| D3-06 | Nada se guarda sin confirmación del usuario | IA | humano | P | – |
| D3-07 | Sin conexión se degrada a registro manual | IA | humano | P | – |
| D3-08 | Cuota de análisis por usuario | IA | humano | P | – |
| D3-09 | Búsqueda por embeddings queda fuera del MVP 3 | IA | humano | P | – |
| D3-10 | Muestras reales de comprobantes y libretas | – | humano | P | – |

Estados: **P** pendiente · **A** aceptada · **R** rechazada.

## 5. Decisiones de sesiones anteriores (referencia)

Para el MVP 1 y el MVP 2 las decisiones ya están en [DECISIONS.md](DECISIONS.md) (D-01 a D-48) y en [MVP2.md §6.4](MVP2.md). Su registro de quién las aceptó es el campo **(P)/(A)** de cada una.
