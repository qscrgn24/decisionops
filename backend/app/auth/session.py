from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.deps import get_db
from app.auth.models import User

COOKIE_NAME = "session_token"
COOKIE_TTL_SECONDS = 60 * 60 * 24 * 14   # 14 days
SECRET_ENV_KEY = "DO_SESSION_SECRET"
SIGNING_SALT = "decisionops-session-v1"


def _b64url_encode(b: bytes):
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

def _b64url_decode(s: str):
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("utf-8"))
    
def _get_secret():
    secret = os.getenv(SECRET_ENV_KEY)
    if not secret:
        raise RuntimeError(f"Missing env var: {SECRET_ENV_KEY}. Set it to a long random value (32+ chars)")
    return secret.encode("utf-8")

def _sign(message: bytes):
    secret = _get_secret()
    key = hashlib.sha256(secret + SIGNING_SALT.encode("utf-8")).digest()
    sig = hmac.new(key, message, hashlib.sha256).digest()
    return _b64url_encode(sig)

def _encode_token(payload: dict):
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = _b64url_encode(raw)
    sig = _sign(raw)
    return f"{body}.{sig}"

def _decode_token(token:str):
    try:
        body_b64, sig = token.split(".", 1)
        raw = _b64url_decode(body_b64)
        expected = _sign(raw)
        if not hmac.compare_digest(expected, sig):
            return None
        payload =  json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception:
        return None



def set_session_cookie(response: Response, user_id: int):
    """
    Creates a signed cookie that stores:
      - uid: user id
      - iat: issued at (unix)
      - exp: expires at (unix)
    """

    now = int(time.time())
    payload = {"uid": user_id, "iat": now, "exp": now + COOKIE_TTL_SECONDS}
    token = _encode_token(payload)

    secure_cookie = settings.ENV.lower() in {"production", "prod", "production_debug"}

    response.set_cooke(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_TTL_SECONDS,
        http_only=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")


def _get_user_id_from_request(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    
    payload = _decode_token(token)
    if not payload:
        return None
    
    if "uid" not in payload or "exp" not in payload:
        return None
    
    if not isinstance(payload["uid"], int) or not isinstance(payload["exp"], int):
        return None
    
    if int(time.time()) > payload["exp"]:
        return None

    return payload["uid"]


def get_current_user(request: Request, db: Session = Depends(get_db)):
    uid = _get_user_id_from_request(request)
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == uid).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid")

    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)):
    uid = _get_user_id_from_request(request)
    if uid is None:
        return None
    
    user = db.query(User).filter(User.id == uid).first()
    if not user or not user.is_active:
        return None

    return user


