import io
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.auth.router as auth_router
from app.auth.models import User
from app.auth.security import hash_password
from app.models.dataset import Dataset
from app.models.run import Run

_PASSWORD = "StrongPassword123!"


def _sample_csv_bytes() -> bytes:
    csv = """item_id,name,cost,value,risk,category
1,Item A,10,50,0.1,Cat1
2,Item B,20,70,0.2,Cat1
3,Item C,15,40,0.3,Cat2
"""
    return csv.encode("utf-8")


def _signup(
    client: TestClient,
    *,
    email: str,
    username: str,
) -> None:
    response = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "username": username,
            "password": _PASSWORD,
        },
    )

    assert response.status_code == 200, response.text


def _login(
    client: TestClient,
    *,
    identifier: str,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={
            "identifier": identifier,
            "password": _PASSWORD,
        },
    )

    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post(
        "/api/auth/logout"
    )

    assert response.status_code == 200, response.text


def _upload_dataset(
    client: TestClient,
) -> str:
    file = io.BytesIO(
        _sample_csv_bytes()
    )

    response = client.post(
        "/api/datasets/upload",
        data={
            "name": "integrity-test"
        },
        files={
            "file": (
                "test.csv",
                file,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["id"]


def _create_run(
    client: TestClient,
    *,
    dataset_id: str,
) -> str:
    response = client.post(
        "/api/runs",
        json={
            "dataset_id": dataset_id,
            "config": {
                "budget": 30,
                "max_items": 2,
                "lambda_risk": 0.5,
                "objective": "value",
            },
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["id"]


def test_database_rejects_run_with_missing_dataset(
    client: TestClient,
    db: Session,
) -> None:
    _signup(
        client,
        email="fk@example.com",
        username="fkuser",
    )

    user = (
        db.query(User)
        .filter(
            User.email == "fk@example.com"
        )
        .one()
    )

    run = Run(
        id=str(uuid.uuid4()),
        user_id=user.id,
        dataset_id=str(uuid.uuid4()),
        status="created",
        config_json={},
        result_json=None,
        error=None,
    )

    db.add(run)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


def test_deleting_dataset_cascades_its_runs(
    client: TestClient,
    db: Session,
) -> None:
    _signup(
        client,
        email="cascade@example.com",
        username="cascadeuser",
    )

    dataset_id = _upload_dataset(client)
    run_id = _create_run(
        client,
        dataset_id=dataset_id,
    )

    response = client.delete(
        f"/api/datasets/{dataset_id}"
    )

    assert response.status_code == 204

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id
        )
        .first()
    )

    run = (
        db.query(Run)
        .filter(
            Run.id == run_id
        )
        .first()
    )

    assert dataset is None
    assert run is None


def test_deleting_run_preserves_dataset(
    client: TestClient,
    db: Session,
) -> None:
    _signup(
        client,
        email="run-delete@example.com",
        username="rundeleteuser",
    )

    dataset_id = _upload_dataset(client)
    run_id = _create_run(
        client,
        dataset_id=dataset_id,
    )

    response = client.delete(
        f"/api/runs/{run_id}"
    )

    assert response.status_code == 204

    run = (
        db.query(Run)
        .filter(
            Run.id == run_id
        )
        .first()
    )

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id
        )
        .first()
    )

    assert run is None
    assert dataset is not None


def test_user_cannot_delete_another_users_data(
    client: TestClient,
    db: Session,
) -> None:
    _signup(
        client,
        email="owner@example.com",
        username="owneruser",
    )

    dataset_id = _upload_dataset(client)
    run_id = _create_run(
        client,
        dataset_id=dataset_id,
    )

    _logout(client)

    _signup(
        client,
        email="other@example.com",
        username="otheruser",
    )

    dataset_response = client.delete(
        f"/api/datasets/{dataset_id}"
    )

    run_response = client.delete(
        f"/api/runs/{run_id}"
    )

    assert dataset_response.status_code == 404
    assert run_response.status_code == 404

    assert (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id
        )
        .first()
        is not None
    )

    assert (
        db.query(Run)
        .filter(
            Run.id == run_id
        )
        .first()
        is not None
    )


def test_missing_delete_targets_return_404(
    client: TestClient,
) -> None:
    _signup(
        client,
        email="missing@example.com",
        username="missinguser",
    )

    missing_id = str(
        uuid.uuid4()
    )

    dataset_response = client.delete(
        f"/api/datasets/{missing_id}"
    )

    run_response = client.delete(
        f"/api/runs/{missing_id}"
    )

    assert dataset_response.status_code == 404
    assert run_response.status_code == 404


def test_delete_endpoints_require_auth(
    client: TestClient,
) -> None:
    missing_id = str(
        uuid.uuid4()
    )

    dataset_response = client.delete(
        f"/api/datasets/{missing_id}"
    )

    run_response = client.delete(
        f"/api/runs/{missing_id}"
    )

    assert dataset_response.status_code in (
        401,
        403,
    )

    assert run_response.status_code in (
        401,
        403,
    )


def test_signup_integrity_race_returns_duplicate_error(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    existing_user = User(
        email="race@example.com",
        username="racewinner",
        password_hash=hash_password(
            _PASSWORD
        ),
    )

    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)

    lookup_results = iter(
        [
            None,
            existing_user,
        ]
    )

    def fake_find_conflicting_user(
        _db: Session,
        *,
        email: str,
        username: str,
    ) -> User | None:
        return next(lookup_results)

    monkeypatch.setattr(
        auth_router,
        "_find_conflicting_user",
        fake_find_conflicting_user,
    )

    def fail_commit() -> None:
        raise IntegrityError(
            "INSERT INTO users",
            {},
            Exception(
                "unique constraint violation"
            ),
        )

    monkeypatch.setattr(
        db,
        "commit",
        fail_commit,
    )

    response = client.post(
        "/api/auth/signup",
        json={
            "email": "race@example.com",
            "username": "raceloser",
            "password": _PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Email already in use."
    }

    assert db.is_active
