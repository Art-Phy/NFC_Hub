
"""User registration and authentication services"""

from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from nfc_hub.core.passwords import hash_password
from nfc_hub.models.user import User



class EmailAlreadyRegisteredError(ValueError):
    """Raised when attempting to register an existing email address"""



def _normalize_email(email: str) -> str:
    """Return an email normalized for storage and comparison"""

    return email.strip().lower()



def register_user(
        db: DatabaseSession,
        *,
        email: str,
        password: str,
) -> User:
    """Create a user with a securely hashed password"""

    normalized_email = _normalize_email(email)

    existing_user_id = db.execute(
        select(User.id).where(
            User.email == normalized_email
        )
    ).scalar_one_or_none()

    if existing_user_id is not None:
        raise EmailAlreadyRegisteredError(
            "Email address is already registered"
        )

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
    )

    db.add(user)
    db.flush()

    return user
