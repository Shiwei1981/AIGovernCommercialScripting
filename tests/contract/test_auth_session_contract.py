def test_auth_login_contract(client):
    resp = client.get("/auth/login", allow_redirects=False)
    assert resp.status_code == 302


def test_auth_login_change_user_contract(client):
    resp = client.get("/auth/login?prompt=select_account", allow_redirects=False)
    assert resp.status_code == 302
    assert "prompt=select_account" in resp.headers["location"]


def test_auth_callback_and_session_contract(client):
    callback = client.get("/auth/callback?mock_user=contract-user", allow_redirects=False)
    assert callback.status_code == 302
    session = client.get("/api/session")
    assert session.status_code == 200
    payload = session.json()
    assert payload["authenticated"] is True
    assert "user_id" in payload["user"]
    assert payload["user"]["user_principal_name"] == "contract-user@example.test"
