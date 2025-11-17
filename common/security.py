from __future__ import annotations

from passlib.context import CryptContext

from common.errors import ValidationError


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a raw password and return the bcrypt digest."""
    normalized = plain_password.strip()
    if len(normalized) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    return _pwd_context.hash(normalized)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a raw password against its bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)
