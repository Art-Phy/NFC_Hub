
"""Session creation service"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy import delete, select

from nfc_hub.core.settings import AppSettings, get_settings
from nfc_hub.core.tokens import generate_csrf_token, generate_session_token, hash_session_token
from nfc_hub.models.session import Session as SessionModel



@dataclass(frozen=True)
class CreatedSession:
    """Session record together with its client-side credentials"""

    session: SessionModel
    session_token: str
    csrf_token: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """Return a datetime normalized to timezone-aware UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def create_session(db: DatabaseSession, *, user_id: int | None = None, settings: AppSettings | None = None) -> CreatedSession:
    """Create an anonymous or authenticated database session"""

    app_settings = settings or get_settings()
    session_token = generate_session_token()
    csrf_token = generate_csrf_token()

    ttl_seconds = (
        app_settings.authenticated_session_ttl_seconds
        if user_id is not None
        else app_settings.anonymous_session_ttl_seconds
    )

    session = SessionModel(
        token_hash=hash_session_token(session_token),
        csrf_token=csrf_token,
        user_id=user_id,
        expires_at=_utc_now() + timedelta(seconds=ttl_seconds),
    )

    db.add(session)
    db.flush()

    return CreatedSession(
        session=session,
        session_token=session_token,
        csrf_token=csrf_token,
    )



def get_valid_session(
    db: DatabaseSession,
    session_token: str,
) -> SessionModel | None:
    """Return the matching session when it exists and has not expired."""

    token_hash = hash_session_token(session_token)

    session = db.execute(
        select(SessionModel).where(
            SessionModel.token_hash == token_hash
        )
    ).scalar_one_or_none()

    if session is None:
        return None

    if _as_utc(session.expires_at) <= _utc_now():
        return None

    return session



def delete_session(
        db: DatabaseSession,
        session_token: str,
) -> bool:
    """Delete the session matching a client-side token"""

    token_hash = hash_session_token(session_token)

    session = db.execute(
        select(SessionModel).where(
            SessionModel.token_hash == token_hash
        )
    ).scalar_one_or_none()

    if session is None:
        return False

    db.delete(session)
    db.flush()

    return True



def delete_expired_sessions(db: DatabaseSession) -> int:
    """Delete expired sessions and return the affected row count"""

    result = db.execute(
        delete(SessionModel)
        .where(SessionModel.expires_at <= _utc_now())
        .execution_options(synchronize_session=False)
    )

    return result.rowcount
