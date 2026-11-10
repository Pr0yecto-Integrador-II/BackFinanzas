# language: es

Característica: Lectura del historial en voz alta (HU19)
  Como usuario que consulta su historial
  Quiero que la lectura continua renueve su autorización y omita lo eliminado
  Para escuchar solo movimientos vigentes sin cortes

  Escenario: Renovar el token durante una lectura larga no agota la cuota
    Dado que inicié sesión con "ana@correo.com"
    Cuando renuevo el token de voz 7 veces durante la lectura
    Entonces todas las renovaciones de voz son exitosas

  Escenario: Un movimiento eliminado llega marcado para omitirlo de la lectura
    Dado que inicié sesión con "ana@correo.com"
    Y tengo 3 gastos sincronizados en "Alimentación"
    Cuando elimino por sincronización el segundo gasto
    Entonces el pull marca ese gasto como eliminado
    Y los otros 2 gastos siguen vigentes para leer
