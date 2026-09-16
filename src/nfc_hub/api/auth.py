
"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

from nfc_hub.core.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

from nfc_hub.core.dependencies import get_db, require_csrf_token
from nfc_hub.core.session_service import create_session, delete_session
from nfc_hub.models.session import Session as SessionModel
from nfc_hub.core.settings import get_settings
from nfc_hub.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


def _set_session_cookie(
    response: Response,
    session_token: str,
) -> None:
    """Store a session token in a secure HTTP-only cookie"""

    settings = get_settings()

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.authenticated_session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )



def _clear_session_cookie(response: Response) -> None:
    """Remove the session cookie from the client"""

    settings = get_settings()

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )



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

    _set_session_cookie(
        response,
        created_session.session_token,
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        csrf_token=created_session.csrf_token,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: DatabaseSession = Depends(get_db),
) -> AuthResponse:
    """Authenticate a user and create a new session"""

    try:
        user = authenticate_user(
            db,
            email=str(payload.email),
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
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

    _set_session_cookie(
        response,
        created_session.session_token,
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        csrf_token=created_session.csrf_token,
    )



@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    response: Response,
    _current_session: SessionModel = Depends(require_csrf_token),
    db: DatabaseSession = Depends(get_db),
) -> None:
    """Revoke the current session and remove its cookie"""

    settings = get_settings()
    session_token = request.cookies.get(settings.session_cookie_name)

    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid session required",
        )

    try:
        delete_session(db, session_token)
        db.commit()
    except Exception:
        db.rollback()
        raise

    _clear_session_cookie(response)
