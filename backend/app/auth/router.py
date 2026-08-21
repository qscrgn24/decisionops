# ruff: noqa: B008
from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import AuthResponse, LoginRequest, SignUpRequest, UserOut
from app.auth.security import hash_password, verify_password
from app.auth.session import (
    clear_session_cookie,
    get_current_user,
    get_optional_user,
    set_session_cookie,
)
from app.db.deps import get_db
from app.dependencies.rate_limit import limit_auth_read, limit_login, limit_signup

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_username(username: str) -> str:
    return username.strip()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _find_conflicting_user(db: Session, *, email: str, username: str) -> User | None:
    return db.query(User).filter(or_(User.email == email, User.username == username)).first()


def _raise_duplicate_user_error(existing_user: User, *, email: str) -> NoReturn:
    if existing_user.email == email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use.")

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already in use.")


@router.post("/signup", response_model=AuthResponse, dependencies=[Depends(limit_signup)])
def signup(payload: SignUpRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(payload.email)
    username = _normalize_username(payload.username)

    if " " in username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username cannot contain spaces.")

    # Check if email or username already exists
    existing_user = _find_conflicting_user(db, email=email, username=username)

    if existing_user is not None:
        _raise_duplicate_user_error(existing_user, email=email)

    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Create new user
    new_user = User(email=email, username=username, password_hash=password_hash)

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_user = _find_conflicting_user(db, email=email, username=username)
        
        if existing_user is not None:
            _raise_duplicate_user_error(existing_user, email=email)

        raise

    db.refresh(new_user)

    set_session_cookie(response, new_user.id, new_user.session_version)

    return AuthResponse(user=UserOut.model_validate(new_user))


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(limit_login)])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    identifier = payload.identifier.strip()
    identifier_email = identifier.lower() if "@" in identifier else None

    user = db.query(User).filter(or_(User.email == identifier_email, User.username == identifier)).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    set_session_cookie(response, user.id, user.session_version)

    return AuthResponse(user=UserOut.model_validate(user))


@router.get("/me", response_model=AuthResponse, dependencies=[Depends(limit_auth_read)])
def me(user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/logout")
def logout(response: Response, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    if user is not None:
        user.session_version += 1
        db.commit()

    clear_session_cookie(response)

    return {"ok": True}
