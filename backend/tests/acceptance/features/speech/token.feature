# language: es

Característica: Autorización segura del servicio de voz (HU16)
  Como usuario autenticado
  Quiero que la app obtenga una autorización temporal para los servicios de voz
  Para usar dictado y lectura sin exponer credenciales en el navegador

  Escenario: Obtención exitosa de token temporal de voz
    Dado que inicié sesión con "ana@correo.com"
    Cuando solicito un token de voz
    Entonces recibo un token temporal con región "eastus" y vigencia de 600 segundos
    Y la respuesta no se guarda en caché

  Escenario: Límite de solicitudes excedido al pedir tokens de voz
    Dado que inicié sesión con "ana@correo.com"
    Y ya solicité 30 tokens de voz en la última hora
    Cuando solicito un token de voz
    Entonces la respuesta de voz es 429 con código "SPEECH_RATE_LIMITED"
    Y el mensaje de voz es "Has alcanzado el límite temporal del servicio de voz. Intenta más tarde"

  Escenario: Servicio de voz no configurado o caído en el servidor
    Dado que inicié sesión con "ana@correo.com"
    Y el proveedor de voz no responde
    Cuando solicito un token de voz
    Entonces la respuesta de voz es 503 con código "SPEECH_SERVICE_UNAVAILABLE"
    Y el mensaje de voz es "El servicio de voz no está disponible en este momento"

  Escenario: Sin sesión no se emite token de voz
    Cuando solicito un token de voz sin sesión
    Entonces la respuesta de voz es 401
