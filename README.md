
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Web_API-009688)
![Tests](https://img.shields.io/badge/Tests-199_Passing-success)
![Version](https://img.shields.io/badge/Version-v0.6.0-orange)
![Status](https://img.shields.io/badge/Status-Early_Development-yellow)

## NFC Hub

Aplicación web para gestionar etiquetas NFC reutilizables mediante enlaces permanentes y destinos configurables.

Cada etiqueta física almacenará una URL pública generada por NFC Hub. Su propietario podrá cambiar posteriormente el destino asociado desde la aplicación sin necesidad de volver a escribir la etiqueta.

> NFC Hub sigue en desarrollo. El registro y la autenticación de usuarios ya funcionan; la gestión de etiquetas, destinos y enlaces públicos todavía está pendiente.

---

### Estado actual

La aplicación incluye:

- API desarrollada con FastAPI y documentación interactiva.
- Endpoint de estado `GET /health`.
- Configuración centralizada mediante `AppSettings` y variables `NFC_HUB_`.
- Persistencia con SQLAlchemy 2.x y migraciones reversibles con Alembic.
- Modelos persistentes `User` y `Session`.
- Registro, inicio de sesión, cierre de sesión y consulta del usuario actual.
- Contraseñas almacenadas mediante hashes Argon2id.
- Sesiones persistentes identificadas mediante tokens aleatorios; la base de datos almacena únicamente su hash SHA-256.
- Cookies de sesión `HttpOnly`, `SameSite=lax` y `Secure` configurable, obligatorio en producción.
- Caducidad configurable para sesiones anónimas y autenticadas.
- Protección CSRF mediante la cabecera `X-CSRF-Token` en el cierre de sesión.
- Comprobación de origen y tipo de contenido en registro e inicio de sesión.
- Respuestas de autenticación con `Cache-Control: no-store`.
- Suite de 199 tests, incluidos recorridos HTTP completos con una base de datos temporal.

La gestión de etiquetas NFC y la resolución de sus enlaces permanentes serán incrementos posteriores.

---

### Requisitos

- Python 3.10 o superior.
- pip.
- Entorno virtual recomendado.

---

### Instalación

Clona el repositorio y entra en su directorio:

```bash
git clone https://github.com/Art-Phy/NFC_Hub
cd NFC_Hub
```

Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala el proyecto en modo editable con las dependencias de testing:

```bash
python3 -m pip install -r requirements.txt
```

`requirements.txt` instala `.[test]` según la configuración de `pyproject.toml`. La instalación editable permite trabajar sobre `src/nfc_hub` sin reinstalar el paquete tras cada cambio de código.

---

### Configuración

La configuración está definida en `src/nfc_hub/core/settings.py`. Los ajustes pueden sobrescribirse mediante variables de entorno con el prefijo `NFC_HUB_`.

| Ajuste | Valor predeterminado | Uso |
|---|---|---|
| `NFC_HUB_APP_NAME` | `NFC Hub` | Nombre mostrado por FastAPI. |
| `NFC_HUB_ENVIRONMENT` | `development` | Entorno de ejecución. |
| `NFC_HUB_DEBUG` | `false` | Modo de depuración. |
| `NFC_HUB_DATABASE_URL` | `sqlite:///./nfc_hub.db` | Conexión a la base de datos. |
| `NFC_HUB_SESSION_COOKIE_NAME` | `nfc_hub_session` | Nombre de la cookie de sesión. |
| `NFC_HUB_SESSION_COOKIE_SECURE` | `false` | Exige HTTPS para enviar la cookie cuando está activado. |
| `NFC_HUB_AUTHENTICATED_SESSION_TTL_SECONDS` | `2592000` | Duración de una sesión autenticada: 30 días. |
| `NFC_HUB_ANONYMOUS_SESSION_TTL_SECONDS` | `900` | Duración de una sesión anónima: 15 minutos. |
| `NFC_HUB_AUTH_ALLOWED_ORIGINS` | `["http://localhost:8000", "http://127.0.0.1:8000"]` | Orígenes admitidos para registro e inicio de sesión cuando la petición incluye `Origin`. |

Ambos TTL deben ser positivos. La configuración impide iniciar la aplicación con `NFC_HUB_ENVIRONMENT=production` si `NFC_HUB_SESSION_COOKIE_SECURE` no está activado.

Ejemplo para desarrollo local:

```bash
export NFC_HUB_ENVIRONMENT="development"
export NFC_HUB_DATABASE_URL="sqlite:///./nfc_hub.db"
export NFC_HUB_AUTH_ALLOWED_ORIGINS='["http://localhost:8000","http://127.0.0.1:8000"]'
```

Los orígenes son valores exactos formados por protocolo, dominio y puerto; no llevan rutas ni barra final. Antes de usar otro dominio, configura expresamente su origen. No habilites CORS con credenciales para orígenes arbitrarios.

La versión de FastAPI se obtiene de los metadatos del paquete instalado. Si cambias la versión en `pyproject.toml`, reinstala el proyecto para actualizar esos metadatos:

```bash
python3 -m pip install -e ".[test]"
```

---

### Base de datos y migraciones

La conexión y la factoría de sesiones están en `src/nfc_hub/core/database.py`. Los modelos se encuentran en `src/nfc_hub/models/`.

`User` almacena el correo normalizado, el hash de contraseña, el estado activo y las fechas de creación y actualización. `Session` vincula opcionalmente una sesión con un usuario y almacena el hash del token, el token CSRF y su caducidad.

Antes de iniciar la aplicación, aplica las migraciones pendientes:

```bash
alembic upgrade head
```

Para comprobar si los modelos presentan cambios pendientes de migración:

```bash
alembic check
```

Para consultar la revisión aplicada:

```bash
alembic current
```

Para revertir todas las migraciones en una base de datos **desechable**:

```bash
alembic downgrade base
```

No ejecutes `downgrade base` sobre una base de datos cuyos usuarios o sesiones quieras conservar.

---

### Ejecución

Desde la raíz del repositorio, después de aplicar las migraciones:

```bash
uvicorn nfc_hub.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.

- Estado: `http://127.0.0.1:8000/health`
- Documentación interactiva: `http://127.0.0.1:8000/docs`

El endpoint de estado devuelve:

```json
{
  "status": "ok"
}
```

---

### Autenticación

| Método y ruta | Función | Resultado |
|---|---|---|
| `POST /auth/register` | Crea un usuario y una sesión autenticada. | `201`, usuario público, token CSRF y cookie de sesión. |
| `POST /auth/login` | Comprueba las credenciales y crea una nueva sesión. | `200`, usuario público, token CSRF y cookie de sesión. |
| `GET /auth/me` | Consulta el usuario de la sesión actual y su token CSRF. | `200` o `401` si no hay sesión válida. |
| `POST /auth/logout` | Revoca la sesión actual y borra la cookie. | `204`; exige `X-CSRF-Token`. |

El registro exige un correo válido y una contraseña de entre 8 y 128 caracteres. El inicio de sesión acepta cualquier contraseña no vacía de hasta 128 caracteres para poder comprobar cuentas existentes.

Registro e inicio de sesión requieren `Content-Type: application/json`. Si el cliente envía una cabecera `Origin`, esta debe coincidir exactamente con uno de los orígenes configurados. Los clientes HTTP sin esa cabecera también pueden utilizar la API enviando JSON.

Una respuesta correcta de registro o inicio de sesión tiene esta forma:

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com"
  },
  "csrf_token": "token-csrf-generado"
}
```

El token de sesión se entrega en una cookie `HttpOnly`; no aparece en el JSON. La contraseña y su hash tampoco se devuelven. Para cerrar sesión, el cliente envía el `csrf_token` recibido en la cabecera `X-CSRF-Token`.

`GET /auth/me` permite recuperar el usuario y el CSRF de una sesión válida después de recargar la aplicación. No crea una sesión nueva.

#### Ejemplo local con curl

Con la aplicación iniciada en `http://127.0.0.1:8000`, registra un usuario y guarda la cookie:

```bash
curl -i \
  -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure-password"}' \
  http://127.0.0.1:8000/auth/register
```

Consulta la sesión usando esa cookie:

```bash
curl -i \
  -b cookies.txt \
  http://127.0.0.1:8000/auth/me
```

Para cerrar sesión, sustituye el valor de ejemplo por el `csrf_token` recibido al registrarte o al consultar `/auth/me`:

```bash
curl -i \
  -b cookies.txt \
  -c cookies.txt \
  -X POST \
  -H "X-CSRF-Token: TOKEN_CSRF_RECIBIDO" \
  http://127.0.0.1:8000/auth/logout
```

Después del logout, la misma sesión ya no permite acceder a `/auth/me`.

El archivo `cookies.txt` contiene credenciales de sesión durante las pruebas: mantenlo fuera del repositorio.

---

### Seguridad y alcance

- Las contraseñas se verifican con Argon2id y sus hashes pueden actualizarse al iniciar sesión si cambian los parámetros.
- Los correos inexistentes, contraseñas incorrectas y cuentas inactivas reciben el mismo error de credenciales.
- El token de sesión se genera aleatoriamente; solo su hash se almacena en la base de datos.
- Las sesiones caducadas no se aceptan. El servicio permite revocarlas y eliminar registros caducados.
- El cierre de sesión exige un token CSRF asociado a la sesión.
- La cookie utiliza `HttpOnly` y `SameSite=lax`; en producción debe utilizar también `Secure`.
- Los endpoints de autenticación devuelven `Cache-Control: no-store`.

La API todavía está en desarrollo. Antes de exponer registro y login públicamente harán falta HTTPS en el despliegue, limitación de intentos y una configuración de orígenes acorde al dominio real.

---

### Testing

Ejecuta la suite completa desde la raíz del repositorio:

```bash
python3 -m pytest -v
```

La suite actual contiene **199 tests**. Comprueba la configuración, los modelos, las migraciones, el hashing de contraseñas, los tokens, las sesiones, las dependencias de FastAPI, los esquemas y los endpoints de autenticación.

Los tests de integración utilizan una base de datos temporal para verificar el recorrido completo: registro, consulta de sesión, logout, revocación del token, nuevo login, credenciales incorrectas, correo duplicado y protección CSRF. No modifican la base de datos de desarrollo.

---

### Objetivo del proyecto

NFC Hub busca permitir que cada usuario pueda:

1. Crear una cuenta.
2. Registrar sus etiquetas NFC.
3. Asociar cada etiqueta con un destino HTTPS.
4. Escribir una URL permanente en la etiqueta física.
5. Cambiar el destino sin reescribirla.
6. Activar o desactivar sus etiquetas.
7. Gestionar únicamente las etiquetas de su propiedad.

El primer paso, la gestión de cuentas y sesiones, ya está implementado. Las funciones relativas a etiquetas y destinos permanecen pendientes.

---

### Hardware utilizado

El flujo físico inicial se ha validado con:

- Etiquetas NTAG215 reutilizables.
- Registros NDEF con URL HTTPS, texto y otros contenidos.
- Flipper Zero con firmware Momentum.
- Aplicación NFC Maker.
- Dispositivos Android y iPhone.

Las etiquetas admiten escritura y reescritura de registros NDEF y pueden leerse en ambos tipos de dispositivo. Durante la primera fase se escribirán mediante el Flipper Zero; NFC Hub todavía no escribe físicamente las etiquetas.
