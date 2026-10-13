# language: es

Característica: Inicio de sesión (HU02)
  Como usuario registrado
  Quiero iniciar sesión
  Para acceder a mis datos financieros

  Escenario: Login exitoso devuelve token de acceso
    Dado que existe una cuenta con correo "ana@correo.com" y contraseña "clave1234"
    Cuando inicio sesión con correo "ana@correo.com" y contraseña "clave1234"
    Entonces recibo un token de acceso
    Y la respuesta incluye una cookie de refresh httpOnly

  Escenario: Credenciales incorrectas devuelven el mismo mensaje
    Dado que existe una cuenta con correo "ana@correo.com" y contraseña "clave1234"
    Cuando inicio sesión con correo "ana@correo.com" y contraseña "mala"
    Entonces recibo un error 401 con mensaje "Correo o contraseña incorrectos."

  Escenario: Correo inexistente devuelve el mismo mensaje que clave incorrecta
    Dado que no existe ningún usuario registrado
    Cuando inicio sesión con correo "nadie@correo.com" y contraseña "clave1234"
    Entonces recibo un error 401 con mensaje "Correo o contraseña incorrectos."

  Escenario: Bloqueo tras 5 intentos fallidos
    Dado que existe una cuenta con correo "ana@correo.com" y contraseña "clave1234"
    Cuando fallo el login 5 veces con correo "ana@correo.com"
    Y intento iniciar sesión con la clave correcta
    Entonces recibo un error 429 con mensaje "Demasiados intentos. Intenta de nuevo en 15 minutos."
