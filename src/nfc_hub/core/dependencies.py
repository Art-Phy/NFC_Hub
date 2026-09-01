
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DatabaseSession

from nfc_hub.core.database import SessionLocal
from nfc_hub.core.session_service import get_valid_session
from nfc_hub.core.settings import get_settings
from nfc_hub.models.session import Session as SessionModel
from nfc_hub.models.user import User


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



def require_session(
        current_session: SessionModel | None = Depends(get_current_session),
) -> SessionModel:
    """Require a valid anonymous or authenticated session"""

    if current_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid session required",
        )

    return current_session



def require_authenticated_user(
        current_session: SessionModel = Depends(require_session),
) -> User:
    """Require a valid session belonging to an active user"""

    if current_session.user_id is None or current_session.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if not current_session.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_session.user
