![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Web_API-009688)
![Tests](https://img.shields.io/badge/Tests-9_Passing-success)
![Version](https://img.shields.io/badge/Version-v0.3.0-orange)
![Status](https://img.shields.io/badge/Status-Early_Development-yellow)

## NFC Hub

Aplicación web para gestionar etiquetas NFC reutilizables mediante enlaces permanentes y destinos configurables.

Cada etiqueta física almacenará una URL pública generada por NFC Hub. El propietario podrá modificar posteriormente el destino asociado desde la aplicación sin necesidad de volver a escribir la etiqueta.

> NFC Hub se encuentra actualmente en una fase inicial de desarrollo. La gestión de usuarios, etiquetas y destinos todavía no está implementada.

---

### Estado actual

La aplicación incluye actualmente:

- Aplicación mínima desarrollada con FastAPI.
- Endpoint de comprobación de estado `GET /health`.
- Documentación interactiva de FastAPI.
- Configuración centralizada mediante `AppSettings`.
- Variables de entorno con el prefijo `NFC_HUB_`.
- Nombre de la aplicación, entorno y modo debug configurables.
- Versión obtenida desde los metadatos del paquete instalado.
- Pruebas automatizadas con pytest.
- Estructura de paquete basada en `src/`.
- Configuración del proyecto mediante `pyproject.toml`.
- Instalación editable con dependencias de ejecución y testing.
- Ejecución de la aplicación y los tests sin configurar manualmente `PYTHONPATH`.

Respuesta del endpoint de estado:

```json
{
  "status": "ok"
}
```
---

### Requisitos

- Python 3.10 o superior
- pip
- Entorno virtual

---

### Instalación

Clona el repositorio y entra en el directorio del proyecto:

```bash
git clone https://github.com/Art-Phy/NFC_Hub
cd NFC_Hub
```

Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala el proyecto en modo editable junto con las dependencias de desarrollo y testing:

```bash
python3 -m pip install -r requirements.txt
```

El archivo `requirements.txt` instala el proyecto mediante la configuración definida en `pyproject.toml`.

El modo editable permite que los cambios realizados en `src/nfc_hub` estén disponibles inmediatamente sin tener que reinstalar el proyecto.

---

### Configuración

La configuración de la aplicación se encuentra centralizada en:

```text
src/nfc_hub/settings.py
```
Los ajustes pueden modificarse mediante variables de entorno con el prefijo `NFC_HUB_`:

```bash
export NFC_HUB_APP_NAME="NFC Hub Local"
export NFC_HUB_ENVIRONMENT="development"
export NFC_HUB_DEBUG="true"
```
La versión de la aplicación se obtiene directamente desde los metadatos del paquete instalado, evitando mantener una versión duplicada dentro del código.

---

### Uso

Ejecuta la aplicación desde la raíz del repositorio:

```bash
uvicorn nfc_hub.main:app --reload
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

Comprueba su estado mediante `http://127.0.0.1:8000/health`.

La documentación interactiva de FastAPI está disponible en `http://127.0.0.1:8000/docs`.

---

### Testing

Ejecuta la suite completa desde la raíz del repositorio:

```bash
python3 -m pytest -v
```

La configuración de pytest se encuentra centralizada en `pyproject.toml`. Gracias a la instalación editable del proyecto, los tests pueden importar el paquete `nfc_hub` sin configurar manualmente `PYTHONPATH`.

Los tests verifican:

- El código de estado HTTP del endpoint `/health`.
- La respuesta JSON exacta del endpoint.
- Los valores predeterminados de la configuración.
- La obtención de la versión desde los metadatos del paquete.
- La sobrescritura de ajustes mediante variables de entorno.
- La conversión del valor de `NFC_HUB_DEBUG` a tipo booleano.

---

### Objetivo del proyecto

El objetivo de NFC Hub es permitir que un usuario pueda:
1. Crear una cuenta.
2. Registrar una etiquieta NFC.
3. Asociarla con un destino HTTPS.
4. Escribir una URL permanente en la etiqueta física.
5. Cambiar posteriormente su destino sin reescribirla.
6. Activar o desactivar la etiqueta.
7. Gestionar únicamente las etiquetas de su propiedad.

El desarrollo se realizará mendiante incrementos pequeños, revisados y acompañados de pruebas automatizadas.

---

### Hardware utilizado

El flujo físico inicial se está validando con:
- Etiqueta NTAG215.
- Registros NDEF con URL HTTPS.
- Flipper Zero con firmware Momemtum.
- Dispositivo Android
- Dispositivo iPhone.

Durante la primera fase, las etiquetas se escribirán mediante la Flipper Zero. La escritura diracta del NFC Hub no forma parte del alcance inicial.

---

### Licencia

Pendiente de definir.
