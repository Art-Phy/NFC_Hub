
"""Secure token generation, hashing and verification utilities"""

import hashlib
import hmac
import secrets

SESSION_TOKEN_BYTES = 32
CSRF_TOKEN_BYTES = 32



def generate_session_token() -> str:
    """Generate a cryptographically secure session token"""

    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """Return the SHA-256 hexadecimal digest of a session token"""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token"""

    return secrets.token_urlsafe(CSRF_TOKEN_BYTES)


def verify_csrf_token(received_token: str, expected_token: str) -> bool:
    """Compare two CSRF tokens using a timing-safe operation"""

    return hmac.compare_digest(
        received_token.encode("utf-8"),
        expected_token.encode("utf-8"),
    )
