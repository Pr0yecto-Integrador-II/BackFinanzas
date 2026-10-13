# Manual de usuario de BackFinanzas

## 1. ¿Qué es BackFinanzas?

BackFinanzas es una aplicación para registrar gastos e ingresos, organizar movimientos, controlar
presupuestos y entender el comportamiento financiero mensual. Está diseñada para funcionar sin
conexión después del primer inicio de sesión en un dispositivo.

La aplicación usa:

- **movimientos** para registrar gastos e ingresos;
- **categorías** para organizar los movimientos;
- **reglas recurrentes** para pagos o ingresos repetidos;
- **presupuestos** para controlar límites mensuales;
- **sincronización** para mantener los dispositivos actualizados.

> **Estado del repositorio:** este repositorio contiene actualmente el backend de la aplicación. Las
> pantallas y navegación descritas en este manual corresponden al frontend Angular definido en el
> Blueprint y sirven como guía funcional para su uso y validación.

## 2. Primer acceso

### 2.1. Crear una cuenta

1. Abra la pantalla **Registro**.
2. Escriba su correo electrónico.
3. Cree una contraseña de entre 8 y 128 caracteres que contenga al menos una letra y un número.
4. Repita la contraseña.
5. Seleccione la moneda de la cuenta. La opción predeterminada es **COP**.
6. Seleccione **Crear cuenta**.

Al finalizar:

- el correo se guarda en minúsculas y sin espacios exteriores;
- la sesión queda iniciada;
- se crean 12 categorías predeterminadas;
- puede entrar a la pantalla de inicio.

El registro necesita conexión a internet.

### 2.2. Iniciar sesión

1. Abra **Ingresar**.
2. Escriba su correo y contraseña.
3. Seleccione **Iniciar sesión**.

En un dispositivo nuevo se necesita conexión para descargar los datos. Después del primer acceso,
la aplicación puede abrirse sin conexión y mostrar la información local.

Por seguridad, los errores de correo y contraseña muestran el mismo mensaje. Después de cinco
intentos fallidos dentro de quince minutos, el acceso se bloquea temporalmente.

## 3. Pantalla de inicio

La pantalla de inicio muestra el resumen del mes:

- total de ingresos;
- total de gastos;
- balance;
- categorías con mayor gasto;
- presupuestos próximos a su límite;
- cambios pendientes de sincronización;
- indicador de conexión.

El resumen se calcula con los datos locales disponibles. Si hay cambios pendientes, se mostrarán
cuando el dispositivo vuelva a conectarse y complete la sincronización.

## 4. Registrar un gasto o ingreso

1. Abra **Movimientos**.
2. Seleccione **Nuevo movimiento**.
3. Elija **Gasto** o **Ingreso**.
4. Introduzca el monto.
5. Seleccione una categoría del mismo tipo.
6. Elija la fecha.
7. Agregue, si lo necesita, una descripción, una nota o etiquetas.
8. Seleccione **Guardar**.

El movimiento se guarda primero en el dispositivo. No es necesario esperar una respuesta del
servidor para continuar trabajando.

### 4.1. Montos

Los montos se muestran con el formato de la moneda elegida, pero el sistema los conserva como
centavos enteros. No introduzca valores negativos para representar el tipo: use **Gasto** o
**Ingreso**.

### 4.2. Fecha y tipo

- No se permiten fechas futuras.
- La categoría debe corresponder al tipo del movimiento.
- El tipo de un movimiento no puede cambiarse después de guardarlo.

## 5. Editar y eliminar movimientos

### Editar

1. Abra **Movimientos**.
2. Seleccione el movimiento.
3. Cambie los campos permitidos.
4. Seleccione **Guardar cambios**.

### Eliminar

1. Abra el movimiento.
2. Seleccione **Eliminar**.
3. Confirme la operación.

La eliminación es lógica: el movimiento deja de mostrarse como activo, pero se conserva la
información necesaria para sincronizar correctamente todos los dispositivos.

## 6. Buscar y filtrar el historial

En **Movimientos** puede:

- buscar por descripción o nota;
- filtrar por tipo;
- filtrar por categoría;
- filtrar por rango de fechas;
- consultar movimientos con etiquetas;
- ordenar el historial.

Los filtros se ejecutan sobre los datos locales del dispositivo y siguen disponibles sin conexión.

## 7. Categorías

Abra **Categorías** para crear, editar o eliminar categorías personalizadas.

Las categorías se dividen en:

- categorías de gasto;
- categorías de ingreso.

Al crear una categoría, use un nombre descriptivo. El sistema ignora diferencias de mayúsculas y
tildes para evitar duplicados como `Comida`, `comida` y `Comída`.

No se puede eliminar la última categoría de un tipo. Si una categoría tiene movimientos, reglas o
presupuestos asociados:

1. Seleccione **Eliminar**.
2. Elija una categoría de destino del mismo tipo.
3. Confirme la reasignación.

Los elementos asociados se trasladan a la categoría de destino en una sola operación.

## 8. Etiquetas y notas

Las etiquetas ayudan a agrupar movimientos sin crear categorías nuevas.

- Puede usar hasta cinco etiquetas por movimiento.
- Las etiquetas se normalizan a minúsculas.
- El símbolo `#` inicial se elimina automáticamente.
- Las etiquetas repetidas se guardan una sola vez.

Las notas son texto libre asociado al movimiento y no modifican el cálculo financiero.

## 9. Movimientos recurrentes

Abra **Recurrentes** para configurar una plantilla:

1. Seleccione el tipo de movimiento.
2. Indique el monto y la categoría.
3. Seleccione la frecuencia.
4. Defina la fecha de inicio.
5. Opcionalmente, defina una fecha final o un número máximo de repeticiones.
6. Elija si los movimientos se generan automáticamente o quedan **Por confirmar**.
7. Guarde la regla.

Las ocurrencias próximas se consultan en **Recurrentes > Próximos**. Las ocurrencias generadas
usan un identificador determinista para no duplicarse si la aplicación procesa la misma fecha más
de una vez.

Una regla puede pausarse o eliminarse. El borrado es lógico y no elimina los movimientos históricos
que ya se hayan generado.

## 10. Presupuestos

Abra **Presupuestos** y seleccione una categoría de gasto:

1. Seleccione el mes de vigencia.
2. Introduzca el límite mensual.
3. Seleccione **Guardar**.

Solo puede existir un presupuesto activo por categoría y mes. El presupuesto debe empezar el primer
día del mes.

La aplicación muestra:

- monto presupuestado;
- monto gastado;
- porcentaje utilizado;
- alerta al alcanzar el 80 %;
- alerta al alcanzar el 100 % o superar el límite.

Modificar un presupuesto no cambia los movimientos ya registrados.

## 11. Gráficos y resumen

En **Gráficos** puede consultar la distribución de gastos por categoría y comparar meses.

Los gráficos se calculan desde la base local del navegador. Si todavía existen cambios sin
sincronizar, el resultado puede cambiar cuando la sincronización reciba información de otro
dispositivo.

## 12. Trabajar sin conexión

Cuando no haya internet:

- aparecerá el indicador **Sin conexión**;
- podrá consultar sus datos locales;
- podrá registrar, editar y eliminar información;
- podrá crear cambios que quedarán pendientes en la cola de sincronización.

Cada escritura se guarda junto con su cambio pendiente. Cuando vuelva la conexión, la aplicación
envía los cambios y descarga los realizados en otros dispositivos.

Si un cambio es rechazado por una regla de negocio, se mostrará el motivo para que pueda corregirlo.
Un cambio rechazado no impide sincronizar los demás cambios válidos.

## 13. Cerrar sesión

Abra **Ajustes** y seleccione **Cerrar sesión**.

Si hay cambios pendientes, la aplicación mostrará una advertencia indicando cuántos cambios se
perderían. Confirme solo después de sincronizar o de aceptar la pérdida.

Al cerrar sesión:

- se invalida la sesión del servidor;
- se eliminan los datos locales del dispositivo;
- se elimina la información de la cuenta de ese navegador.

En **Ajustes** también está disponible **Cerrar sesión en todos los dispositivos**.

## 14. Recuperar la contraseña

1. Abra **Recuperar contraseña**.
2. Introduzca el correo de la cuenta.
3. Revise el correo recibido.
4. Abra el enlace antes de que caduque.
5. Escriba y confirme la nueva contraseña.

Por seguridad, la aplicación muestra el mismo mensaje aunque el correo no esté registrado. Los
enlaces son de un solo uso y caducan después de 30 minutos.

## 15. Indicadores y errores frecuentes

| Mensaje o situación | Qué significa | Qué hacer |
|---|---|---|
| **Sin conexión** | El dispositivo no puede contactar al servidor | Continúe trabajando; sincronizará después |
| **Cambios pendientes** | Hay datos locales aún no enviados | Recupere conexión y espere la sincronización |
| **Demasiados intentos** | Se alcanzó el límite de login | Espere 15 minutos antes de reintentar |
| **La fecha no puede ser futura** | La fecha del movimiento no es válida | Seleccione hoy o una fecha anterior |
| **Categoría incompatible** | La categoría no coincide con gasto/ingreso | Elija una categoría del mismo tipo |
| **Cambio rechazado** | El servidor rechazó una operación de sincronización | Abra el detalle y corrija los datos |

## 16. Buenas prácticas

- Use una contraseña única y no la comparta.
- Cierre sesión en equipos compartidos.
- Mantenga la aplicación conectada periódicamente para sincronizar.
- No elimine datos del navegador manualmente si existen cambios pendientes.
- Use categorías estables y etiquetas para facilitar los análisis.
- Revise los presupuestos al inicio de cada mes.

## 17. Espacio reservado para el pipeline de integración y despliegue

Esta sección se completará cuando se defina el proceso operativo de publicación.

| Dato | Valor |
|---|---|
| Entorno de pruebas | ____________________ |
| Entorno de producción | ____________________ |
| URL publicada | ____________________ |
| Canal de soporte | ____________________ |
| Fecha de la última revisión | ____________________ |
| Responsable | ____________________ |

Antes de publicar una versión, el procedimiento deberá indicar como mínimo:

- cómo se ejecutan las migraciones;
- cómo se verifica `/health`;
- cómo se validan las pruebas;
- cómo se gestiona una migración fallida;
- cómo se revierte una versión;
- cómo se informa una interrupción o una sincronización pendiente.
