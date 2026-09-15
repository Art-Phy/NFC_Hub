
"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

from nfc_hub.core.auth_service import (
    EmailAlreadyRegisteredError,
    register_user,
)
from nfc_hub.core.dependencies import get_db
from nfc_hub.core.session_service import create_session
from nfc_hub.core.settings import get_settings
from nfc_hub.schemas.auth import (
    AuthResponse,
    RegisterRequest,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: DatabaseSession = Depends(get_db),
) -> AuthResponse:
    """Register a user and create an authenticated session."""

    try:
        user = register_user(
            db,
            email=str(payload.email),
            password=payload.password,
        )
    except (EmailAlreadyRegisteredError, IntegrityError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        ) from exc

    try:
        created_session = create_session(
            db,
            user_id=user.id,
        )
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    settings = get_settings()

    response.set_cookie(
        key=settings.session_cookie_name,
        value=created_session.session_token,
        max_age=settings.authenticated_session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        csrf_token=created_session.csrf_token,
    )
