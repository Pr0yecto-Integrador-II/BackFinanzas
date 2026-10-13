# language: es

Característica: Gestión de categorías (HU08)
  Como usuario autenticado
  Quiero organizar mis movimientos por categorías
  Para clasificar mejor mis finanzas

  Escenario: El registro crea 12 categorías predeterminadas visibles en el primer pull
    Dado que tengo una sesión activa con "ana@correo.com"
    Cuando hago el primer pull
    Entonces recibo exactamente 12 categorías
    Y 9 son de tipo "expense" y 3 de tipo "income"

  Escenario: Eliminar categoría con movimientos exige destino de reasignación
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo una categoría de tipo "expense" con un movimiento registrado
    Cuando borro esa categoría sin indicar destino
    Entonces el cambio es rechazado con código "ReassignmentRequiredError"

  Escenario: Eliminar categoría con reasignación mueve los movimientos
    Dado que tengo una sesión activa con "ana@correo.com"
    Y tengo dos categorías de tipo "expense"
    Y la primera tiene un movimiento registrado
    Cuando borro la primera categoría reasignando a la segunda
    Entonces el movimiento ahora pertenece a la segunda categoría
    Y la primera categoría aparece con "deleted" en true

  Escenario: Cada usuario solo ve sus propias categorías
    Dado que existen dos usuarios "ana@correo.com" y "luis@correo.com"
    Cuando ana hace pull
    Entonces solo ve sus 12 categorías, no las de luis
