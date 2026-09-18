
from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DatabaseSession
from typing import Annotated

from nfc_hub.core.database import SessionLocal
from nfc_hub.core.session_service import get_valid_session
from nfc_hub.core.settings import get_settings
from nfc_hub.core.tokens import verify_csrf_token
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



def require_csrf_token(
        current_session: SessionModel = Depends(require_session),
        csrf_token: Annotated[
            str | None,
            Header(alias="X-CSRF-Token"),
        ] = None,
) -> SessionModel:
    """Require a valid CSRF token for the current session"""

    if csrf_token is None or not verify_csrf_token(
        csrf_token,
        current_session.csrf_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    return current_session



def require_safe_auth_request(request: Request) -> None:
    """Require JSON and reject untrusted authentication origins."""

    content_type = request.headers.get("content-type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()

    if media_type != "application/json":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be application/json",
        )

    origin = request.headers.get("origin")

    if origin is not None:
        settings = get_settings()

        if (
            origin == "null"
            or origin not in settings.auth_allowed_origins
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Untrusted request origin",
            )
