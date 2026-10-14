# language: es

Característica: Sincronización sin conexión (HU04 + sync)
  Como usuario con varios dispositivos
  Quiero que mis datos se sincronicen
  Para verlos en cualquier dispositivo

  Escenario: El pull devuelve solo los cambios nuevos desde la última versión
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Y hago un pull inicial y anoto la versión
    Cuando registro un nuevo gasto
    Y hago pull desde la versión anotada
    Entonces solo recibo el nuevo gasto

  Escenario: El pull pagina los resultados
    Dado que tengo una sesión activa con "ana@correo.com"
    Cuando hago pull con límite de 5
    Entonces recibo 5 cambios y "has_more" es true
    Y puedo pedir la siguiente página con "next_since"

  Escenario: Reglas recurrentes y presupuestos viajan por sync
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Cuando registro una regla recurrente mensual y un presupuesto por sync
    Entonces el pull incluye las entidades "recurring_rule" y "budget"

  Escenario: Un lote de más de 500 cambios es rechazado completo
    Dado que tengo una sesión activa con "ana@correo.com"
    Cuando envío un lote de 501 cambios
    Entonces la respuesta es un error de validación 422

  Escenario: Cada usuario solo puede modificar sus propios datos
    Dado que existen dos usuarios "ana@correo.com" y "luis@correo.com"
    Y ana tiene una categoría y un movimiento
    Cuando luis intenta usar la categoría de ana o pisar el id del movimiento de ana
    Entonces ambos intentos son rechazados
