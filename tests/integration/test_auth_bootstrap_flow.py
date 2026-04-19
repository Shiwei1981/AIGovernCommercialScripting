import os

import pytest
from fastapi.testclient import TestClient


def test_unauthenticated_blocking(client: TestClient):
    resp = client.get("/api/products/bootstrap")
    assert resp.status_code == 401


def test_post_login_default_behavior(auth_client: TestClient):
    products = auth_client.get("/api/products/bootstrap")
    assert products.status_code == 200
    assert len(products.json()) == 10


def test_mock_auth_rejected_when_not_test(monkeypatch: pytest.MonkeyPatch):
    os.environ.update(
        {
            "APP_ENV": "dev",
            "MOCK_AUTH_ENABLED": "true",
            "AZURE_TENANT_ID": "tenant-test",
            "AZURE_CLIENT_ID": "client-test",
            "AZURE_CLIENT_SECRET": "secret-test",
            "OIDC_AUTHORITY_URL": "https://login.microsoftonline.com/tenant-test/v2.0",
            "OIDC_CALLBACK_URL_TEST": "http://localhost:8000/auth/callback",
            "SQL_SERVER": "server.database.windows.net",
            "SQL_DATABASE": "db",
            "OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "OPENAI_API_VERSION": "2024-10-21",
            "OPENAI_DEPLOYMENT": "gpt-4o-mini",
            "GOOGLE_NEWS_RSS_BASE_URL": "https://news.google.com/rss/search",
        }
    )
    from app.config import load_settings

    with pytest.raises(RuntimeError):
        load_settings()
