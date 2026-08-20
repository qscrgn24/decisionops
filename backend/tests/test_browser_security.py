import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_security_headers_are_added(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200

    assert response.headers["content-security-policy"] == (
            "default-src 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "object-src 'none'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

    assert response.headers["cross-origin-opener-policy"] == "same-origin"
    assert response.headers["cross-origin-resource-policy"] == "same-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"

    assert "strict-transport-security" not in response.headers


def test_hsts_is_enabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENV", "production")

    app = create_app()

    with TestClient(app) as production_client:
        response = production_client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"


def test_cross_site_origin_is_blocked_for_post(client: TestClient) -> None:
    response = client.post("/api/auth/logout", headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Cross-site request blocked"}

    assert response.headers["x-frame-options"] == "DENY"


def test_cross_site_fetch_metadata_is_blocked(client: TestClient) -> None:
    response = client.post("/api/auth/logout", headers={"Origin": "http://localhost:5173", "Sec-Fetch-Site": "cross-site"})

    assert response.status_code == 403


def test_allowed_origin_can_make_post_request(client: TestClient) -> None:
    response = client.post("/api/auth/logout", headers={"Origin": "http://localhost:5173", "Sec-Fetch-Site": "same-site"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_non_browser_post_without_origin_is_allowed(client: TestClient) -> None:
    response = client.post("/api/auth/logout")

    assert response.status_code == 200


def test_untrusted_host_is_rejected(client: TestClient) -> None:
    response = client.get("/api/health", headers={"Host": "evil.example"})

    assert response.status_code == 400


def test_allowed_cors_preflight_succeeds(client: TestClient) -> None:
    response = client.options("/api/auth/logout", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_disallowed_cors_preflight_is_rejected(client: TestClient) -> None:
    response = client.options("/api/auth/logout", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"})

    assert response.status_code == 400

    assert "access-control-allow-origin" not in response.headers
