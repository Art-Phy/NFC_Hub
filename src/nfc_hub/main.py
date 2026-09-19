from fastapi import FastAPI

from nfc_hub.api.auth import router as auth_router
from nfc_hub.core.settings import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
)

app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}
