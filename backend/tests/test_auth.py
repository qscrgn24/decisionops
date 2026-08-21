def test_signup_login_me_logout(client, signup_and_login):
    signup_and_login()

    r = client.get("/api/auth/me")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["email"] == "test@example.com"

    r = client.post("/api/auth/logout")
    assert r.status_code == 200, r.text

    r = client.get("/api/auth/me")
    assert r.status_code in (401, 403), r.text
