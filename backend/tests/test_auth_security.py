import time

import pytest
from fastapi.testclient import TestClient
from passlib.hash import argon2
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.security import hash_password
from app.auth.session import COOKIE_NAME, _decode_token, _encode_token


def _get_test_user(db: Session, email: str = "test@example.com") -> User:
    return db.query(User).filter(User.email == email).one()


def _replace_session_cookie(client: TestClient, token: str) -> None:
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, token)


def test_signup_issues_versioned_session_cookie(client: TestClient, signup_and_login) -> None:
    signup_and_login()

    token = client.cookies.get(COOKIE_NAME)

    assert token is not None

    payload = _decode_token(token)

    assert payload is not None
    assert set(payload) == {"uid", "sv", "iat", "exp"}
    assert payload["sv"] == 1


def test_legacy_session_cookie_remains_valid_for_initial_version(client: TestClient, db: Session, signup_and_login) -> None:
    signup_and_login()

    user = _get_test_user(db)
    now = int(time.time())

    legacy_token = _encode_token({"uid": user.id, "iat": now, "exp": now + 60})

    _replace_session_cookie(client, legacy_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 200


def test_tampered_session_cookie_is_rejected(client: TestClient, signup_and_login) -> None:
    signup_and_login()

    token = client.cookies.get(COOKIE_NAME)

    assert token is not None

    body, signature = token.split(".", 1)

    replacement = "A" if signature[-1] != "A" else "B"

    tampered_token = f"{body}.{signature[:-1]}{replacement}"

    _replace_session_cookie(client, tampered_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_malformed_session_cookie_is_rejected(client: TestClient) -> None:
    _replace_session_cookie(client, "%%%invalid%%%.signature")

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_expired_session_cookie_is_rejected(client: TestClient, db: Session, signup_and_login) -> None:
    signup_and_login()

    user = _get_test_user(db)
    now = int(time.time())

    expired_token = _encode_token({"uid": user.id, "sv": user.session_version, "iat": now - 120, "exp": now - 60})

    _replace_session_cookie(client, expired_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_future_issued_session_cookie_is_rejected(client: TestClient, db: Session, signup_and_login) -> None:
    signup_and_login()

    user = _get_test_user(db)
    now = int(time.time())

    issued_at = now + 120

    future_token = _encode_token({"uid": user.id, "sv": user.session_version, "iat": issued_at, "exp": issued_at + 60})

    _replace_session_cookie(client, future_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_session_cookie_with_unknown_claim_is_rejected(client: TestClient, db: Session, signup_and_login) -> None:
    signup_and_login()

    user = _get_test_user(db)
    now = int(time.time())

    token = _encode_token({"uid": user.id, "sv": user.session_version, "iat": now, "exp": now + 60, "role": "admin"})

    _replace_session_cookie(client, token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_boolean_user_id_is_rejected(client: TestClient) -> None:
    now = int(time.time())

    token = _encode_token({"uid": True, "sv": 1, "iat": now, "exp": now + 60})

    _replace_session_cookie(client, token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_inactive_user_session_is_rejected(client: TestClient, db: Session, signup_and_login) -> None:
    signup_and_login()

    user = _get_test_user(db)

    user.is_active = False
    db.commit()

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_logout_revokes_previous_session_cookie(client: TestClient, db: Session, signup_and_login) -> None:
    signup_and_login()

    stolen_token = client.cookies.get(COOKIE_NAME)

    assert stolen_token is not None

    user = _get_test_user(db)
    original_version = user.session_version

    response = client.post("/api/auth/logout")

    assert response.status_code == 200

    db.refresh(user)

    assert user.session_version == original_version + 1

    _replace_session_cookie(client, stolen_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_signup_rejects_password_below_new_minimum(client: TestClient) -> None:
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "short@example.com",
            "username": "shortpassword",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 422


def test_hash_password_rejects_password_below_new_minimum() -> None:
    with pytest.raises(ValueError, match="at least 15"):
        hash_password("StrongPass123!")


def test_existing_short_password_can_still_login(client: TestClient, db: Session) -> None:
    legacy_password = "StrongPass123!"

    user = User(email="legacy@example.com", username="legacyuser", password_hash=argon2.hash(legacy_password))

    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post(
        "/api/auth/login",
        json={
            "identifier": "legacy@example.com",
            "password": legacy_password,
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "legacy@example.com"
    assert client.cookies.get(COOKIE_NAME) is not None
