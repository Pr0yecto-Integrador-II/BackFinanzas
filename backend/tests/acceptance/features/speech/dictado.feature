# language: es

Característica: Movimientos registrados por dictado de voz (HU17)
  Como usuario de la app
  Quiero que los movimientos que dicto y confirmo se sincronicen igual que los manuales
  Para no perder las validaciones de HU04 y HU05

  Escenario: Dictar un gasto completo y sincronizarlo tras confirmar
    Dado que inicié sesión con "ana@correo.com"
    Cuando sincronizo el gasto dictado "Gasté veinticinco mil pesos en almuerzo en Alimentación"
    Entonces el pull trae un gasto de 2500000 centavos en "Alimentación" con descripción "Almuerzo"
    Y el movimiento tiene versión asignada por el servidor

  Escenario: Dictar un ingreso válido
    Dado que inicié sesión con "ana@correo.com"
    Cuando sincronizo el ingreso dictado "Recibí tres millones quinientos mil pesos de Salario"
    Entonces el pull trae un ingreso de 350000000 centavos en "Salario"

  Escenario: Un borrador dictado con monto cero se rechaza
    Dado que inicié sesión con "ana@correo.com"
    Cuando sincronizo un gasto dictado en "Ocio" con monto 0
    Entonces el movimiento dictado es rechazado con código "InvalidAmountError"

  Escenario: Un borrador dictado con fecha futura se rechaza
    Dado que inicié sesión con "ana@correo.com"
    Cuando sincronizo un gasto dictado en "Ocio" con fecha "2999-01-01"
    Entonces el movimiento dictado es rechazado con código "FutureDateError"

  Escenario: Un dictado con categoría de otro tipo se rechaza
    Dado que inicié sesión con "ana@correo.com"
    Cuando sincronizo un gasto dictado en la categoría de ingreso "Salario"
    Entonces el movimiento dictado es rechazado con código "CategoryTypeMismatchError"

  Escenario: Pulsar dos veces "Guardar" no duplica el movimiento dictado
    Dado que inicié sesión con "ana@correo.com"
    Cuando sincronizo dos veces el mismo gasto dictado en "Transporte"
    Entonces solo existe un movimiento dictado
