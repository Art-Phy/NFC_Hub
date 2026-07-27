
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
- Pruebas automatizadas con pytest.
- Estructura inicial basada en `src/`.

Respuesta del endpoint de estado:

```json
{
  "status": "ok"
}
```

###Requisitos

- Python 3.10 o superior
- pip
- Entorno virtual

---

### Instalación

Clona el repositorio y entra en el directorio del proyecto:
```bash
git clone <URL_REPOSITORIO>
cd NFC_Hub
```

Crea y activa un entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala dependencias
```bash
python3 -m pip install -r requirements.txt
```

---

### Uso

Ejecuta la apliación desde la raíz del repositorio
```bash
PYTHONPATH=src uvicorn nfc_hub.main:app --reload
```

La aplicación estará disponible en `http://127.0.0.1:8000`

Comprueba su estado mendiante `http://127.0.0.1:8000/health`

La documentación interactiva de FastAPI está disponible en `http://127.0.0.1:8000/docs`

---

### Testing

Ejecuta la suite completa desde la raíz del repositorio
```bash
PYTHONPATH=src python3 -m pytest -v
```

Los tests verifican:
- El código de estado HTTP del endpoint **/health**.
- La respuesta JSON exacta del endpoint.

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
