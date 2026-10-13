# language: es

Característica: Recuperación de contraseña (HU03)
  Como usuario que olvidó su contraseña
  Quiero recibir un enlace de recuperación
  Para restablecer mi acceso

  Escenario: Solicitar recuperación con correo existente envía el correo
    Dado que existe una cuenta con correo "ana@correo.com" y contraseña "clave1234"
    Cuando solicito recuperar contraseña con correo "ana@correo.com"
    Entonces la respuesta es exitosa
    Y se envió un correo de recuperación

  Escenario: La respuesta es idéntica aunque el correo no exista
    Dado que no existe ningún usuario registrado
    Cuando solicito recuperar contraseña con correo "nadie@correo.com"
    Entonces la respuesta es exitosa
    Y no se envió ningún correo

  Escenario: Flujo completo de restablecimiento revoca sesiones anteriores
    Dado que existe una cuenta con correo "ana@correo.com" y contraseña "clave1234"
    Y tengo una sesión activa
    Cuando solicito recuperar contraseña con correo "ana@correo.com"
    Y restablezco la contraseña con el token recibido a "nueva1234"
    Entonces mi sesión anterior ya no es válida
    Y puedo iniciar sesión con la nueva contraseña "nueva1234"

  Escenario: El token de recuperación solo funciona una vez
    Dado que existe una cuenta con correo "ana@correo.com" y contraseña "clave1234"
    Cuando solicito recuperar contraseña con correo "ana@correo.com"
    Y restablezco la contraseña con el token recibido a "nueva1234"
    Y vuelvo a usar el mismo token
    Entonces recibo un error con mensaje "Este enlace ya no es válido."
