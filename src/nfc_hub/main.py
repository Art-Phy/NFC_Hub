from fastapi import FastAPI

from nfc_hub.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
)


@app.get("/health")
def health():
    return {"status": "ok"}
