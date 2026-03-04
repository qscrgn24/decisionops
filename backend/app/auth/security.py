from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False