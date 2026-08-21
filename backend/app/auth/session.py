# ruff: noqa: B008
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, cast

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.config import settings
from app.db.deps import get_db

COOKIE_NAME = "session_token"
COOKIE_TTL_SECONDS = 60 * 60 * 24 * 14   # 14 days
SIGNING_SALT = "decisionops-session-v1"

_MAX_TOKEN_CHARS = 2048
_CLOCK_SKEW_SECONDS = 60

_CURRENT_CLAIMS = frozenset({"uid", "sv", "iat", "exp"})
_LEGACY_CLAIMS = frozenset({"uid", "iat", "exp"})


@dataclass(frozen=True)
class _SessionClaims:
    user_id: int
    session_version: int
    issued_at: int
    expires_at: int


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    if not value:
        raise ValueError("Empty base64 value.")

    padding = "=" * (-len(value) % 4)

    return base64.b64decode((value + padding).encode("ascii"), altchars=b"-_", validate=True)

def _get_secret() -> bytes:
    return settings.DO_SESSION_SECRET.encode("utf-8")


def _sign(message: bytes) -> str:
    secret = _get_secret()

    key = hashlib.sha256(secret + SIGNING_SALT.encode("utf-8")).digest()
    signature = hmac.new(key, message, hashlib.sha256).digest()

    return _b64url_encode(signature)


def _encode_token(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    body = _b64url_encode(raw)
    signature = _sign(raw)

    return f"{body}.{signature}"


def _decode_token(token: str) -> dict[str, object] | None:
    if not token or len(token) > _MAX_TOKEN_CHARS or token.count(".") != 1:
        return None

    try:
        body_b64, supplied_signature = token.split(".", 1)

        raw = _b64url_decode(body_b64)
        expected_signature = _sign(raw)

        if not hmac.compare_digest(expected_signature, supplied_signature):
            return None

        payload =  json.loads(raw.decode("utf-8"))

        if not isinstance(payload, dict):
            return None

        if not all(isinstance(key, str) for key in payload):
            return None

        return cast(dict[str, object], payload)

    except (UnicodeDecodeError, UnicodeEncodeError, ValueError, TypeError, json.JSONDecodeError):
        return None


def _parse_sesssion_claims(payload: dict[str, object]) -> _SessionClaims | None:
    keys = frozenset(payload)

    if keys == _CURRENT_CLAIMS:
        session_version = payload["sv"]

    elif keys == _LEGACY_CLAIMS:
        # Sessions issued before server-side revocation support
        # implicitly belong to the initial session version
        session_version = 1

    else:
        return None

    user_id = payload["uid"]
    issued_at = payload["iat"]
    expires_at = payload["exp"]

    values = (user_id, session_version, issued_at, expires_at)

    if not all(type(value) is int for value in values):
        return None

    user_id = cast(int, user_id)
    session_version = cast(int, session_version)
    issued_at = cast(int, issued_at)
    expires_at = cast(int, expires_at)

    if user_id <= 0:
        return None

    if session_version <= 0:
        return None

    if issued_at < 0 or expires_at < 0:
        return None

    if expires_at <= issued_at:
        return None

    if expires_at - issued_at > COOKIE_TTL_SECONDS:
        return None

    now = int(time.time())

    if issued_at > now + _CLOCK_SKEW_SECONDS:
        return None

    if now >= expires_at:
        return None

    return _SessionClaims(user_id=user_id, session_version=session_version, issued_at=issued_at, expires_at=expires_at)


def set_session_cookie(response: Response, user_id: int, session_version: int) -> None:
    if user_id <= 0:
        raise ValueError("User ID must be positive.")

    if session_version <= 0:
        raise ValueError("Session version must be positive.")

    now = int(time.time())
    payload = {"uid": user_id, "sv": session_version, "iat": now, "exp": now + COOKIE_TTL_SECONDS}

    token = _encode_token(payload)

    secure_cookie = settings.ENV.lower() in {"production", "prod", "production_debug"}

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_TTL_SECONDS,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def _get_session_claims_from_request(request: Request) -> _SessionClaims | None:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return None

    payload = _decode_token(token)

    if not payload:
        return None

    return _parse_sesssion_claims(payload)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    claims = _get_session_claims_from_request(request)

    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.get(User, claims.user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid")

    if user.session_version != claims.session_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Invalid")

    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    claims = _get_session_claims_from_request(request)

    if claims is None:
        return None

    user = db.get(User, claims.user_id )

    if not user or not user.is_active:
        return None

    if user.session_version != claims.session_version:
        return None

    return user


