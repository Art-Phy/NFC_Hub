
from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session as DatabaseSession

from nfc_hub.core.database import SessionLocal
from nfc_hub.core.session_service import get_valid_session
from nfc_hub.core.settings import get_settings
from nfc_hub.models.session import Session as SessionModel


def get_db() -> Generator[DatabaseSession, None, None]:
    """Provide a database session and close it after the request"""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()



def get_current_session(
        request: Request,
        db: DatabaseSession = Depends(get_db),
) -> SessionModel | None:
    """Return the valid session indentified by the request cookie"""

    settings = get_settings()
    session_token = request.cookies.get(settings.session_cookie_name)

    if session_token is None:
        return None

    return get_valid_session(db, session_token)
