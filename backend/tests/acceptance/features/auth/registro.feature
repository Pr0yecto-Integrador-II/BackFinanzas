# language: es

Característica: Registro de usuario (HU01)
  Como usuario nuevo
  Quiero registrarme con correo y contraseña
  Para poder usar la aplicación

  Escenario: Registro exitoso devuelve sesión y crea categorías por defecto
    Dado que no existe ningún usuario registrado
    Cuando me registro con correo "maria@correo.com" y contraseña "Clave1234"
    Entonces recibo un token de acceso
    Y el correo del perfil es "maria@correo.com"
    Y se crean 12 categorías por defecto

  Escenario: No puedo registrarme con un correo ya existente
    Dado que ya existe una cuenta con correo "maria@correo.com"
    Cuando me registro con correo "maria@correo.com" y contraseña "Clave1234"
    Entonces recibo un error con código "EmailAlreadyRegisteredError"

  Escenario: La contraseña debe tener al menos una letra y un número
    Dado que no existe ningún usuario registrado
    Cuando me registro con correo "b@correo.com" y contraseña "sololetras"
    Entonces recibo un error con código "WeakPasswordError"

  Escenario: No se puede enviar campos extra en el registro
    Dado que no existe ningún usuario registrado
    Cuando me registro con un campo extra "id" con valor "forzado"
    Entonces la respuesta es un error de validación 422
