# Registro de decisiones

Formato: contexto → decisión → razón → consecuencia. Una decisión que cambie una regla del Blueprint se propone primero allí. Estado: **P** propuesta, **A** aceptada.

---

### D-01 · Código en `backend/` dentro de este repo (P)
- **Decisión:** `backend/` en la raíz, con `docker-compose.yml` y `docs/` al lado.
- **Razón:** el Blueprint y `AGENTS.md` fijan esa estructura; así el frontend puede sumarse como `frontend/` sin mover nada.
- **Consecuencia:** si prefieres el código en la raíz del repo, se cambia ahora y no después.

### D-02 · Python 3.12 con `uv` (A)
- **Razón:** el Blueprint pide 3.12+ y comandos `uv run`. El sistema trae 3.11, pero `uv` descarga 3.12 sin tocar el sistema.

### D-03 · Monolito modular hexagonal (A, del Blueprint)
- Dentro de cada módulo: `api → application → domain ← infrastructure`. El dominio es Python puro (dataclasses, `Protocol` como puertos).
- **Razón:** lo exige el Blueprint; además hace probables las reglas de negocio sin base de datos.
- **Regla de fronteras:** un módulo solo usa la capa `application` de otro. Eliminar una categoría (HU08) mueve movimientos, reglas y presupuestos, así que `categories` llamará a puertos que `transactions`, `recurring` y `budgets` exponen en su `application`, nunca a sus tablas.

### D-04 · Dinero en `BIGINT` de centavos (A, del Blueprint)
- Nunca `float`. El esquema de entrada de la API recibe `amount_minor` entero.
- El formato local ("1.250.000") es asunto del frontend; el backend no interpreta cadenas de dinero.

### D-05 · Tokens de sesión (P)
- **Decisión:** access token JWT de vida corta (15 min) en el cuerpo de la respuesta; refresh token opaco aleatorio en cookie `httpOnly; Secure; SameSite=Strict`, guardado como SHA-256 en `refresh_tokens`.
- **Rotación con familias:** cada `/auth/refresh` revoca el token usado y emite uno nuevo con +30 días (deslizante, HU02 regla 2). Si llega un token ya revocado, se revoca toda la familia (robo).
- **Razón:** el Blueprint define `family_id`, `revoked_at` y cookie httpOnly. El JWT corto evita consultar la BD en cada petición; la cookie protege el refresh de XSS.
- **Abierto:** los 15 min son mi valor por defecto; el Blueprint no lo fija.

### D-06 · Contraseñas con Argon2id vía `pwdlib` (A, del Blueprint)
- Validación (8–128, letra y número) en el dominio. Se compara siempre contra un hash falso si el correo no existe, para que el tiempo de respuesta no revele qué cuentas existen (HU02 regla 3).

### D-07 · Límites con Redis y un puerto `RateLimiter` (P)
- Login: 5 fallos / 15 min por (correo, IP) → bloqueo 15 min. Recuperación: 3 / hora por correo (HU03 regla 4).
- **Razón:** el Blueprint lo asigna a Redis. El puerto permite un adaptador en memoria en las pruebas unitarias, y las de integración usan Redis real del compose.
- Al solicitar recuperación, la respuesta es idéntica exista o no la cuenta, **también cuando se excede el límite** (no se filtra información); solo se deja de enviar el correo.

### D-08 · Tokens de recuperación (A)
- 32 bytes aleatorios (`secrets.token_urlsafe`), se guarda solo el SHA-256, vence a los 30 min, un solo uso, y al pedir uno nuevo se marcan usados los anteriores. Restablecer revoca todas las familias de refresh del usuario (HU03 regla 6).

### D-09 · Correo: puerto `EmailSender` + cola ARQ (P)
- **Decisión:** el caso de uso encola el envío en ARQ; el adaptador de desarrollo escribe el enlace en el log, y el de producción (SMTP o Resend) se configura por variables de entorno.
- **Razón:** AGENTS.md exige preguntar antes de depender de un servicio externo. Así se puede construir y probar todo sin elegir proveedor.
- **Seguridad:** el log de desarrollo es el único lugar donde aparece el enlace; en producción nunca se registra.

### D-10 · `version` desde la secuencia global `sync_version_seq` (A, del Blueprint)
- Se toma con `nextval` en **cada** escritura de las cuatro tablas sincronizables, dentro de la misma transacción. El cliente nunca la envía.
- **Riesgo:** con transacciones concurrentes, una versión menor puede confirmarse después de una mayor. Un `pull` que ya avanzó `since` se la saltaría para siempre.
- **Decisión:** serializar los push de un mismo usuario con `pg_advisory_xact_lock` sobre un hash de su `user_id`. Cada usuario solo lee sus propios datos, así que basta con que sus propias escrituras no se solapen. El costo es despreciable en una app personal.

### D-11 · Conflictos: gana el último que llega (A, del Blueprint)
- El push hace upsert por `id`. `user_id` se toma del token; si el `id` ya existe y pertenece a **otro** usuario, el cambio se rechaza (no se pisa ni se revela que existe).
- Excepciones por regla de dominio: el `type` de un movimiento no cambia (HU06); el `type` de una categoría con movimientos tampoco (HU08). Si el push los intenta cambiar, ese cambio se rechaza con su `code`.

### D-12 · Push por cambio, no todo o nada (A, del Blueprint)
- Cada cambio se aplica en su propio `SAVEPOINT`: uno inválido va a `rejected` y no tumba el lote. La respuesta incluye `version` (máxima emitida).
- Orden: categorías → reglas → movimientos → presupuestos, para que las claves foráneas existan.
- Límite de tamaño del lote (propuesta: 500 cambios) para acotar la transacción y el bloqueo de D-10.

### D-13 · `sync` no toca tablas ajenas (A, del Blueprint)
- El push despacha cada cambio al caso de uso del módulo dueño (`UpsertTransaction`, etc.), de modo que **las mismas reglas valen por la API y por la sincronización**.
- El pull sí lee las cuatro tablas, mediante un puerto de lectura `ChangesSince` que cada módulo implementa. Así `sync` no importa modelos ajenos.

### D-14 · Fecha futura y fechas actuales con `Clock` (A, del Blueprint)
- La fecha futura se valida en el dominio con `Clock`. **El servidor no conoce la zona horaria del usuario**: con "hoy UTC" estricto se rechazaría un gasto legítimo de alguien al este de UTC a primeras horas del día. Por eso se admite hasta **hoy UTC + 1 día**.
- **Razón:** el cliente ya impide fechas futuras en su zona; el servidor solo debe evitar abusos. Si prefieres estrictez, se cambia con una línea.
- **Estado:** propuesta; **desvía levemente** del texto del Blueprint ("no puede ser futura"), por eso queda a tu decisión.

### D-15 · Categorías predeterminadas se crean en la transacción del registro (A)
- Las 12 categorías de HU01 se insertan en la misma transacción que el usuario: si algo falla, no queda una cuenta sin categorías. `auth` llama al caso de uso `CreateDefaultCategories` de `categories` (D-03).
- Sus UUID los genera el servidor; el cliente las recibe por `pull`.

### D-16 · Eliminar categoría con reasignación, atómico (A, del Blueprint 6.3.5)
- Una sola transacción: mueve movimientos, reglas y presupuestos a la categoría destino y marca `deleted_at`. Cada fila movida recibe una `version` nueva para que el `pull` de otros dispositivos la vea.
- Presupuestos en conflicto: se conserva el de la categoría destino y el de la origen se borra lógicamente.
- Rechazos: destino de otro tipo o inexistente, y última categoría del tipo (HU08 regla 6).
- **Cómo viaja por sync:** como el push es por cambio y esto toca varias entidades, `delete` de categoría admite `data.reassign_to`. **Ajuste del contrato** sobre la tabla 6.4 del Blueprint; lo dejo para que lo confirmes.

### D-17 · Esquemas estrictos (A, del Blueprint)
- Pydantic v2 con `extra="forbid"`, longitudes y rangos. Errores de dominio → HTTP 422 con `code` y `message`. Errores de validación de forma los devuelve FastAPI en su formato estándar.
- Texto de la API de cara al usuario, en español.

### D-18 · Pruebas contra PostgreSQL real (A)
- `TEXT[]`, GIN, índices parciales, `CHECK` y secuencias no existen en SQLite. Se usa el Postgres del compose; cada prueba de integración corre en una transacción que se revierte o en un esquema limpio.
- **Razón:** una prueba verde contra otro motor no demuestra nada sobre las restricciones que el Blueprint define.

### D-19 · Sin dependencias extra a las del Blueprint (A)
- Solo las de la sección 5 más lo mínimo de herramientas (`uvicorn`, `pydantic-settings`, `email-validator`, `asyncpg`). Cualquier otra se pregunta primero, según AGENTS.md.

### D-20 · Sin commits ni push si no se piden (A, del Blueprint 7.2)
- El trabajo queda en el árbol de trabajo para que lo revises. Los commits usarán Conventional Commits en español con la HU, solo cuando lo indiques.

### D-21 · Puertos 5433 (Postgres) y 6380 (Redis) en el compose (A)
- **Razón:** en esta máquina 5432 y 6379 ya los usa otro proyecto. Usar puertos distintos evita choques y no toca ese otro servicio.
- **Consecuencia:** `DATABASE_URL` y `REDIS_URL` por defecto apuntan a esos puertos (`backend/.env.example`).

### D-22 · `uv` sin empaquetar el proyecto (A)
- `package = false` en `pyproject.toml`: es una aplicación, no una librería. Las pruebas importan `app` con `pythonpath = ["."]`.
- `AGENTS.md` y `CLAUDE.md` se copiaron literalmente del Blueprint (secciones 7.1 y 7.2).

### D-23 · `version` y `updated_at` los fija un trigger de PostgreSQL (A)
- **Decisión:** un trigger `BEFORE INSERT OR UPDATE` en las 4 tablas sincronizables ejecuta `NEW.version := nextval('sync_version_seq')` y `NEW.updated_at := now()`.
- **Razón:** el Blueprint exige que `version` se tome en **cada** escritura y que el cliente nunca la invente. Con un trigger es imposible olvidarlo en un repositorio, e ignora cualquier valor que se intente enviar. Además, la reasignación al eliminar una categoría (D-16) sube la versión de cada fila movida sin código adicional.
- **Consecuencia:** el servidor no puede escribir `version` ni `updated_at` a mano; probado en `tests/integration/test_schema.py`.

### D-24 · Modelos SQLAlchemy en la capa `infrastructure` de cada módulo (A)
- Cada módulo define sus tablas en `modules/<m>/infrastructure/models.py`; `app/models.py` solo los importa para Alembic. Las FK entre módulos existen a nivel de base de datos (integridad), pero el código de un módulo nunca consulta tablas ajenas (D-03).
- `users` genera su `id` en el servidor (HU01); las demás tablas reciben el UUID del cliente.

### D-25 · Una prueba verifica que modelos y migraciones no se desvíen (A)
- `alembic check` corre en las pruebas: si se cambia un modelo sin nueva migración, la prueba falla. Refuerza la regla de "solo migraciones nuevas, nunca editar una aplicada".
- Las pruebas de integración crean la BD `finanzas_test` desde cero y le aplican las migraciones reales (no `create_all`), así se prueba lo que de verdad se despliega.

### D-26 · Códigos HTTP de los errores de `auth` (A)
- Los errores de dominio siguen siendo 422 con `code` y `message` (Blueprint). Dos excepciones por semántica HTTP: `UnauthorizedError` → **401** (credenciales o sesión inválidas) y `TooManyRequestsError` → **429** (bloqueo de login).
- **Razón:** el cliente Angular necesita distinguir "sesión caducada" (ir a login) de "dato inválido" (mostrar mensaje). Con todo en 422 tendría que leer el `code` para decidir algo tan básico.
- Los mensajes de HU01–HU03 están en español y el de credenciales es idéntico para correo inexistente, clave errónea y correo mal formado.

### D-27 · Detalles de implementación de sesiones (A)
- **Logout y refresh usan la cookie, no el access token:** el access token puede haber vencido mientras la app estuvo sin conexión, y cerrar sesión debe funcionar igual (idempotente, 204).
- **Cookie `refresh_token`:** `HttpOnly`, `SameSite=Strict`, `Path=/auth` (no viaja a ningún otro endpoint) y `Secure` según `COOKIE_SECURE` (verdadero por defecto; solo se pone en falso en desarrollo con http).
- **Rotación atómica:** el refresh bloquea la fila (`SELECT ... FOR UPDATE`) para que dos peticiones simultáneas con el mismo token no logren ambas una sesión nueva.
- **Riesgo aceptado:** si el navegador envía dos refresh a la vez con el mismo token (dos pestañas), el segundo parece un reuso y cierra la sesión. El frontend debe serializar el refresh. Queda anotado para la fase del cliente.
- **Revocación:** un access token ya emitido vale hasta 15 min después de cerrar sesión o cambiar la clave. Es el costo de no consultar la BD en cada petición (D-05).
- **Registro atómico (D-15):** usuario, categorías por defecto y sesión se confirman en un solo commit; hay una prueba que simula un fallo y verifica que no queda nada.

### D-28 · Límite de intentos de login (A)
- Contador por (correo, IP) con ventana fija de 15 min que empieza en el **primer** fallo (el `EXPIRE ... NX` evita que cada fallo la extienda). Al quinto fallo se pone una bandera de bloqueo de 15 min; un login correcto reinicia el contador.
- Con el bloqueo activo se rechaza incluso la clave correcta (HU02) y no se revisa la base de datos.
- **Pendiente de despliegue:** detrás de un proxy, la IP real exige `uvicorn --proxy-headers` y confiar solo en el proxy propio; de lo contrario todos los usuarios compartirían la IP del proxy.

### D-29 · Secreto JWT de al menos 32 caracteres (A)
- `Settings` rechaza un `JWT_SECRET` más corto. **Razón:** HS256 pide una clave de al menos 256 bits y PyJWT ya lo advertía en las pruebas. La aplicación no arranca con un secreto débil en vez de funcionar insegura.

### D-30 · Lista de monedas acotada (P)
- HU01 pide "una lista ISO 4217". Incluí 59 monedas activas frecuentes en `domain/rules.py`, no las ~180 del estándar, para no copiar de memoria una lista larga con riesgo de errores. Agregar una es sumar su código a un conjunto.
- **Tú decides** si quieres la lista completa o dejarla acotada a los mercados objetivo.

### D-31 · Recuperación: el correo sale después del commit (A)
- El token se guarda y confirma **antes** de encolar el correo, para no enviar nunca un enlace que no existe en la base. El enlace viaja en el trabajo de ARQ (Redis); su vida es de 30 min y un solo uso, lo que acota el riesgo.
- En desarrollo el worker escribe el enlace en el log (D-09); sigue pendiente el proveedor real.

### D-32 · `categories` entrega casos de uso, no endpoints (A, del Blueprint 6.4)
- La API del Blueprint no tiene rutas de categorías: se crean, editan y borran por `POST /sync/push`. Por eso el módulo expone `CreateDefaultCategories`, `UpsertCategory` y `DeleteCategory`, y la fase 7 los invoca (D-13).
- **Estos casos de uso no confirman la transacción.** Quien los llama decide: el registro (todo o nada, D-15) y el push (un savepoint por cambio, D-12). Probado: el registro crea las 12 categorías en su misma transacción.

### D-33 · Cómo `categories` reasigna sin tocar tablas ajenas (A)
- `categories` define el puerto `CategoryReferrer` (`is_referenced`, `move`). Cada módulo dueño de `category_id` lo implementa sobre **su propia** tabla (`transactions`, `recurring`, `budgets`), y `app/composition.py` es el único lugar que los conecta.
- **Razón:** cumple D-03 sin que `categories` conozca las otras tablas. Añadir un módulo nuevo que guarde `category_id` es escribir un referrer más.
- La reasignación incluye también las filas **borradas lógicamente**, para que ninguna apunte a una categoría eliminada (un "Deshacer" de HU07 no puede resucitar un movimiento huérfano). El trigger de D-23 les sube la `version` sin código extra.

### D-34 · "Tiene movimientos" incluye reglas recurrentes y presupuestos (P)
- HU08 regla 4 bloquea cambiar el tipo "si la categoría tiene movimientos". Lo apliqué a **cualquier uso**: movimientos, reglas recurrentes o presupuestos, todos sin borrar. Si no, una categoría con presupuesto podría pasar a ingreso y dejar un presupuesto de gasto sobre una categoría de ingreso.
- Es ligeramente más estricto que el texto. Se afloja quitando un referrer de la lista.

### D-35 · Presupuestos al reasignar: "si ambas tenían, gana el destino" (A)
- Lo interpreto literalmente: si el destino tiene **algún** presupuesto activo, los de la categoría eliminada se borran lógicamente; si no tiene ninguno, pasan al destino. No se mezclan vigencias por mes.
- Probado con Postgres real en ambos casos.

### D-36 · Eliminar es idempotente; editar una eliminada falla (A)
- `DeleteCategory` sobre una categoría inexistente, ajena o ya eliminada no hace nada y no falla. Reenviar el mismo push no debe dar error (sync idempotente, 6.4), y una categoría ajena se trata como inexistente para no revelar que existe.
- `UpsertCategory` sobre una eliminada devuelve `CategoryNotFoundError`: así el dispositivo que la editaba sin conexión ve el rechazo en vez de resucitarla en silencio.
- Las operaciones de borrado toman un bloqueo de las filas del usuario (`FOR UPDATE`) para que dos borrados simultáneos no dejen un tipo sin categorías.

### D-37 · Catálogo de íconos y colores definido por mí (P)
- El Blueprint dice "conjunto predefinido" sin listarlo. Definí 30 claves de ícono (nombres de Material Icons) y 15 colores (paleta Tailwind, incluye el `#F97316` del ejemplo del Blueprint) en `categories/domain/catalog.py`. El servidor rechaza cualquier otro valor.
- **Tú decides:** si el frontend ya tiene su propio conjunto, hay que alinearlo con este archivo (o reemplazarlo aquí). Hasta entonces es la fuente de verdad.
- Los íconos y colores de las 12 predeterminadas también salen de ahí (mi elección; el Blueprint solo da los nombres).

### D-38 · `name_key` lo calcula siempre el servidor (A)
- Minúsculas y sin tildes con `NFKD`. El servidor ignora cualquier `name_key` que mande el cliente. **Consecuencia:** "ñ" y "n" colisionan (`año` = `ano`), igual que haría `unaccent`; el frontend debe aplicar exactamente la misma normalización para avisar sin conexión.
- Si la normalización alarga el nombre por encima de 30 caracteres (ligaduras como "ﬃ"), se rechaza el nombre en vez de truncar la clave, porque truncar provocaría falsos duplicados.
- **Defensa en la base:** si dos dispositivos crean el mismo nombre a la vez y se saltan la revisión previa, el índice único parcial lo atrapa y el repositorio lo traduce a `CategoryNameTakenError` (probado).

### D-39 · "Deshacer" revive un movimiento, salvo las ocurrencias recurrentes (P)
- **Conflicto entre dos reglas del Blueprint:** HU07 permite *Deshacer* un borrado (el cliente reenvía el movimiento con el mismo `id`), y HU09 regla 5 dice que una ocurrencia recurrente eliminada u omitida **no se vuelve a generar** (el `id` es determinista, así que otro dispositivo sin conexión podría reenviarla).
- **Decisión:**
  - Un movimiento normal eliminado **se revive** si llega un upsert con su `id` (último cambio gana, 6.4).
  - Una ocurrencia generada por una regla, una vez eliminada en el servidor, **no se revive**: el upsert se rechaza con `OccurrenceDeletedError`.
- **Costo asumido:** si alguien elimina una ocurrencia recurrente y toca "Deshacer" *después* de que el borrado ya se sincronizó, el deshacer se rechaza. Es raro (5 segundos), y la alternativa es que dos dispositivos reproduzcan movimientos que el usuario ya descartó.
- **Tú decides** si prefieres lo contrario. Para el cliente: deshacer una ocurrencia recurrente debe hacerse antes de sincronizar el borrado (el `outbox` puede cancelar el borrado pendiente en vez de reenviarlo).

### D-40 · Qué se valida y qué se conserva al editar (A)
- **Inmutables al editar:** `type` (HU06), `created_at` (ordena el día, HU11; el servidor ignora el que llegue) y `recurring_rule_id` (editar una ocurrencia no cambia su regla, HU09). Un intento de cambiar el tipo o la regla se **rechaza**, no se ignora, para que un error del cliente se note.
- **`pending` exige regla:** un movimiento pendiente de confirmar solo tiene sentido si viene de una regla (HU09 regla 3); si no, `PendingWithoutRuleError`. Confirmar un pendiente es un upsert con `status='confirmed'` (y el monto ajustado).
- **La categoría** debe ser del mismo usuario, estar activa y ser del mismo tipo que el movimiento. Si otro dispositivo la eliminó, el movimiento se rechaza y el dispositivo debe hacer `pull` (la reasignación de HU08 ya movió sus movimientos en el servidor).
- **Fecha:** se aplica D-14 (hoy UTC + 1 día).
- **Textos** se recortan; vacíos se guardan como nulos. Pasarse de 100 (descripción) o 500 (nota) caracteres se **rechaza**, no se trunca.

### D-41 · Etiquetas (HU10) (A)
- Normalización: quitar `#` iniciales, minúsculas, cualquier tramo de espacios pasa a un solo `-`, sin `-` en los bordes ("#Viaje Cartagena" → "viaje-cartagena"). Conserva tildes y otros caracteres.
- Se **deduplican** tras normalizar conservando el orden, y recién entonces se aplica el máximo de 5. Una etiqueta vacía tras normalizar ("#") o de más de 20 caracteres se rechaza.
- **Las sugerencias** de etiquetas ya usadas (HU10 regla 2) y el filtro por etiqueta (HU12) viven en el navegador y no necesitan servidor.

### D-42 · Cómo `transactions` consulta a otros módulos (A)
- Define dos puertos propios: `CategoryLookup` (tipo de una categoría activa del usuario) y `RecurringRuleLookup` (¿existe la regla y es de este usuario?). La primera se adapta sobre la consulta `GetActiveCategory` que expone `categories`; la segunda la implementa `recurring` sobre su propia tabla. `app/composition.py` los conecta (D-03, D-33).
- Una regla **eliminada** sigue valiendo para sus ocurrencias ya registradas (HU09 regla 8), así que `exists` no filtra por `deleted_at`.

### D-43 · Eliminar una regla: qué hace el servidor con sus ocurrencias (P)
- HU09 regla 8 dice que al eliminar la regla "los movimientos ya registrados se conservan y los pendientes sin confirmar se eliminan". El Blueprint no dice **dónde** ocurre.
- **Decisión:** el servidor lo hace en la misma transacción del borrado. `DeleteRule` pide a `transactions` (a través del puerto `PendingOccurrences`, que ese módulo implementa sobre su tabla) que dé de baja lógica los movimientos `pending` de esa regla; los confirmados no se tocan. Cada fila afectada sube su `version`, así el borrado llega a los demás dispositivos por `pull`.
- **Segunda defensa:** un dispositivo sin conexión puede haber generado un pendiente *antes* de enterarse del borrado. Su push ya no crea pendientes de una regla eliminada (`RuleDeletedError`). Los movimientos ya **confirmados** de una regla eliminada siguen aceptándose, porque forman parte del historial (por ejemplo, un cobro automático hecho antes del borrado).
- Cambió el puerto `RecurringRuleLookup` de `transactions`: de "¿existe?" a "¿en qué estado está?" (`active` / `deleted` / `None`).

### D-44 · Validaciones de las reglas que el Blueprint no detalla (P)
- **Fin:** por fecha **o** por repeticiones, nunca ambos (también lo impone un `CHECK` en la base). `end_on` no puede ser anterior a `start_on`; igual a `start_on` vale (una sola ocurrencia).
- **Tope de repeticiones:** `max_occurrences` entre 1 y **100 000**. Lo puse yo para evitar valores absurdos y desbordes; el Blueprint solo exige que sea mayor que 0.
- **`generate_from`:** nunca anterior a `start_on` y **nunca retrocede** al editar. Así una reanudación no puede reabrir las fechas del periodo pausado (HU09 regla 7). Al **crear** puede ser mayor que `start_on`, porque una regla creada, pausada y reanudada sin conexión llega al servidor ya en su estado final.
- **El servidor no calcula fechas:** las reglas de quincenal, fin de mes y 29 de febrero, y el máximo de 366 ocurrencias por ejecución, son del motor del navegador (Blueprint 6.2). Aquí solo se valida y guarda la plantilla.
- Una regla eliminada es definitiva: no hay "deshacer" en HU09, así que editarla devuelve `RuleNotFoundError`.
- La regla puede cambiar de tipo si su categoría coincide (HU09 no lo prohíbe, a diferencia de los movimientos en HU06).

### D-45 · Presupuestos con vigencia (HU14) (P)
- Un presupuesto es un registro `(categoría, monto, effective_from)`. Cambiar el monto «desde octubre» es **crear otro registro** con `effective_from` = 1 de octubre; septiembre conserva el suyo (regla 2). El mes vigente lo resuelve el navegador: el registro más reciente con `effective_from` ≤ mes.
- Solo categorías de gasto, activas y del usuario. `effective_from` debe ser día 1 (se rechaza, no se corrige). Monto entre 1 y 13 dígitos.
- Un solo registro activo por (categoría, mes): otro distinto se rechaza con `DuplicateBudgetError` (antes de que lo haga el índice único, para dar un mensaje claro). Un registro eliminado libera el mes.
- Eliminar es baja lógica e idempotente. Eliminar el registro de un mes hace que ese mes vuelva a regirse por el anterior, si existe.
- Gastado, porcentaje, colores y alertas (80 %/100 %, una vez por mes y categoría) viven en el navegador (`budgetAlerts` está en Dexie): el servidor no calcula nada.

### D-46 · Cómo se aplica el push y se entrega el pull (P)
- **Nombres de entidad:** `category`, `recurring_rule`, `transaction`, `budget` (el Blueprint solo ejemplifica `category` y `transaction`).
- **Orden dentro del lote:** primero todos los *upserts* (categorías → reglas → movimientos → presupuestos) y **después** los borrados en orden inverso. El Blueprint solo fija el orden de aplicación; así un borrado de categoría con `reassign_to` ya ve los movimientos que el mismo lote creó o movió, y borrar una regla descarta los pendientes que el lote acaba de crear.
- **Borrar categoría:** `data: {"reassign_to": "<id>"}`. Si está en uso y falta el destino, se rechaza con `ReassignmentRequiredError`. Los demás borrados no llevan `data`.
- **Validación:** `data` tiene esquema propio por entidad con `extra="forbid"`, enteros estrictos (`25.5` en `amount_minor` se rechaza) y topes generosos de longitud; los límites finos los pone el dominio. Un `data` inválido **rechaza ese cambio** (`InvalidChangeError`, con los nombres de los campos pero nunca sus valores), no el lote. `user_id` jamás se acepta.
- **Un `IntegrityError` inesperado** dentro de un cambio se traduce a `StorageConflictError` y rechaza ese cambio en lugar de tumbar el lote.
- **Respuesta `version`:** la mayor `version` que tiene el usuario en sus cuatro tablas tras aplicar el lote.
- **Lote:** hasta 500 cambios (más es HTTP 422 de validación del lote entero). Se hace un solo `commit` al final; los rechazos no dejan rastro en la base.
- **Pull:** cada módulo lee su tabla (`ModelChangesSource`, siempre con `user_id` del token), `sync` mezcla por `version` y pagina. Incluye filas con baja lógica (`deleted: true`) y las del propio dispositivo. `next_since` es la última `version` entregada, o `since` si no hay novedades.
- **Qué datos viajan:** los campos editables y `created_at`; no `user_id`, `version` ni `updated_at` (la versión va aparte).

### D-47 · Cierre: CI, contrato y revisión de seguridad (P)
- **CI** (`.github/workflows/backend.yml`): ruff, formato, mypy, pytest con `--cov-fail-under=90` y verificación de que `backend/openapi.json` está al día. Postgres y Redis como servicios en los mismos puertos que `docker-compose.yml` (5433/6380), que las pruebas esperan.
- **Contrato:** `uv run python scripts/export_openapi.py` genera `backend/openapi.json` (entrada de `ng-openapi-gen`); `--check` falla si quedó desactualizado.
- **CORS:** solo el origen de `FRONTEND_URL`, con credenciales (la cookie de refresh es httpOnly), métodos GET/POST y cabeceras `Authorization`/`Content-Type`. Sin esto el navegador bloquearía al PWA si se sirve desde otro origen.
- **Correo de desarrollo:** `LogEmailSender` escribe el enlace de recuperación (con su token) en el log. El worker ahora **se niega a arrancar** si `COOKIE_SECURE=true` (producción) hasta que se configure el proveedor real (D-09): falla cerrado en vez de filtrar tokens.
- **Revisado sin hallazgos:** toda consulta filtra por `user_id` del token; ningún esquema acepta `user_id`; todos los esquemas de entrada son `extra="forbid"` con límites; sin SQL por concatenación (el único `text()` con parámetro es el bloqueo); sin `float` en montos; sin `datetime.now()` fuera de `Clock`; secretos solo por entorno (`.env` ignorado por git).
- **Pendientes que no son código:** elegir proveedor de correo (D-09), cabeceras de seguridad y TLS en el proxy de despliegue, y el despliegue en sí (fuera de alcance del plan).

### D-48 · Revisión de robustez: errores hallados y corregidos (P)
- **NUL (`\x00`) en texto → HTTP 500.** PostgreSQL no admite ese carácter; llegaba a la base desde el registro/login (correo) y desde `data` del push. Ahora los esquemas de auth lo rechazan (422) y el push rechaza **ese cambio** (`InvalidChangeError`).
- **`DataError` dentro de un cambio del push** (valor fuera de rango o no representable) tumbaba todo el lote. El savepoint lo traduce a `InvalidChangeError`, igual que ya hacía con `IntegrityError`.
- **`paused_at` sin zona horaria** en una regla ahora se rechaza (`AwareDatetime`), como `created_at`.
- **`GET /sync/pull?since=` mayor que BIGINT** daba 500; ahora 422.
- Pruebas nuevas de sondeo: `tests/integration/sync/test_robustness.py` y `tests/integration/auth/test_probes.py`.
