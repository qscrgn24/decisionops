from __future__ import annotations

from typing import Any

from passlib.context import CryptContext

MIN_NEW_PASSWORD_CHARS = 15
MAX_PASSWORD_CHARS = 128

_pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def validate_new_password(password: str) -> None:
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")

    if len(password) < MIN_NEW_PASSWORD_CHARS:
        raise ValueError(f"Password must be at least {MIN_NEW_PASSWORD_CHARS} characters.")

    if len(password) > MAX_PASSWORD_CHARS:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_CHARS} characters.")


def hash_password(password: str) -> Any:
    validate_new_password(password)
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> Any | bool:
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
