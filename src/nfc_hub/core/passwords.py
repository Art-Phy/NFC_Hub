
"""Password hashing and verification utilities"""

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


_password_hasher = PasswordHasher(
    memory_cost=19_456,
    time_cost=2,
    parallelism=1,
    type=Type.ID,
)



def hash_password(password: str) -> str:
    """Hash a password using Argon2id"""

    return _password_hasher.hash(password)



def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a password matches its stored Argon2id hash"""

    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False



def password_needs_rehash(password_hash: str) -> bool:
    """Return whether a stored hash uses outdated parameters"""

    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True
