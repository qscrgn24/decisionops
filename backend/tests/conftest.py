import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ---- IMPORTANT ----
# Settings are loaded at import time (app.core.config.Settings()).
# So we MUST set required env vars before importing app modules.
os.environ.setdefault("APP_NAME", "DecisionOps-Test")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DO_SESSION_SECRET", "test-secret-do-not-use-in-prod")


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return eng


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def create_test_tables(engine):
    from app.db.base import Base
    import app.auth.models  # noqa: F401
    import app.models.dataset  # noqa: F401
    import app.models.run  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(TestingSessionLocal) -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    from app.main import create_app
    from app.db.deps import get_db

    app = create_app()

    # Override DB dependency to use the in-memory SQLite session
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


# ---- Helpers for auth in tests ----

@pytest.fixture()
def signup_and_login(client: TestClient):
    def _fn(email="test@example.com", username="testuser", password="StrongPass123!"):
        r = client.post("/api/auth/signup", json={
            "email": email,
            "username": username,
            "password": password,
        })
        assert r.status_code == 200, r.text
        # cookie is set by backend in response
        return {"email": email, "username": username, "password": password}

    return _fn