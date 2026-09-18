
"""User registration and authentication services"""
from sqlite3 import IntegrityError as SQLiteIntegrityError

from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy.exc import IntegrityError

from nfc_hub.core.passwords import hash_password, password_needs_rehash, verify_password
from nfc_hub.models.user import User


_DUMMY_PASSWORD_HASH = hash_password(
    "nfc-hub-dummy-password-for-timing-protection"
)


class EmailAlreadyRegisteredError(ValueError):
    """Raised when attempting to register an existing email address"""


class InvalidCredentialsError(ValueError):
    """Raised when authentication credentials cannot be accepted"""



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

    try:
        db.flush()
    except IntegrityError as exc:
        if (
            isinstance(exc.orig, SQLiteIntegrityError)
            and str(exc.orig) == "UNIQUE constraint failed: users.email"
        ):
            raise EmailAlreadyRegisteredError(
                "Email address is already registered"
            ) from exc

        raise

    return user



def authenticate_user(
        db: DatabaseSession,
        *,
        email: str,
        password: str,
) -> User:
    """Authenticate an active user using email and password"""

    normalized_email = _normalize_email(email)

    user = db.execute(
        select(User).where(
            User.email == normalized_email
        )
    ).scalar_one_or_none()

    password_hash = (
        user.password_hash
        if user is not None
        else _DUMMY_PASSWORD_HASH
    )

    password_is_valid = verify_password(
        password,
        password_hash,
    )

    if (
        user is None
        or not password_is_valid
        or not user.is_active
    ):
        raise InvalidCredentialsError(
            "Invalid email or password"
        )

    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.flush()

    return user
