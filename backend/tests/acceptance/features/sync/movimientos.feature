# language: es

Característica: Registro de gastos e ingresos (HU04-HU07, HU10)
  Como usuario autenticado
  Quiero registrar mis movimientos financieros
  Para llevar un control de mis finanzas

  Escenario: Registrar un gasto válido lo guarda y aparece en el pull
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Cuando registro un gasto de 25000 centavos en esa categoría con fecha "2026-10-01"
    Entonces el gasto aparece en el pull con la versión asignada por el servidor

  Escenario: El tipo de un movimiento no se puede cambiar
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Y he registrado un gasto con ese movimiento
    Cuando intento cambiar el tipo del movimiento a "income"
    Entonces el cambio es rechazado con código "TransactionTypeLockedError"

  Escenario: No se puede registrar un gasto con fecha futura
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Cuando registro un gasto con fecha "2999-01-01"
    Entonces el cambio es rechazado con código "FutureDateError"

  Escenario: Las etiquetas se normalizan y deduplan
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Cuando registro un gasto con etiquetas "#Viaje" "#viaje" "#Cartagena"
    Entonces las etiquetas guardadas son "viaje" y "cartagena"

  Escenario: Borrar un movimiento es lógico e idempotente
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Y he registrado un gasto con ese movimiento
    Cuando borro ese movimiento por sync
    Entonces el pull lo muestra con "deleted" en true
    Y borrarlo de nuevo no produce error

  Escenario: Un cambio inválido no tumba el resto del lote
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Cuando envío un lote con un gasto inválido y uno válido
    Entonces solo el válido es aceptado
    Y el inválido aparece en "rejected" con su código de error

  Escenario: Reenviar el mismo cambio no duplica el movimiento
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense"
    Cuando registro el mismo gasto dos veces con el mismo id
    Entonces solo existe un movimiento
