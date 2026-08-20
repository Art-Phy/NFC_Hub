
"""Session creation service"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DatabaseSession

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
