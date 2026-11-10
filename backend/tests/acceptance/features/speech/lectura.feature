# language: es

Característica: Autorización para leer un movimiento en voz alta (HU18)
  Como usuario de la app
  Quiero que la lectura en voz alta use la misma autorización temporal
  Para escuchar mis movimientos sin exponer credenciales

  Escenario: Obtener autorización para leer un movimiento
    Dado que inicié sesión con "ana@correo.com"
    Cuando solicito un token de voz
    Entonces recibo un token temporal con región "eastus" y vigencia de 600 segundos

  Escenario: El backend no recibe la voz de lectura
    Dado que inicié sesión con "ana@correo.com"
    Cuando solicito un token de voz indicando la voz "es-CO-SalomeNeural"
    Entonces la respuesta de voz es 422

  Escenario: Servicio de síntesis no disponible
    Dado que inicié sesión con "ana@correo.com"
    Y el proveedor de voz no responde
    Cuando solicito un token de voz
    Entonces la respuesta de voz es 503 con código "SPEECH_SERVICE_UNAVAILABLE"
