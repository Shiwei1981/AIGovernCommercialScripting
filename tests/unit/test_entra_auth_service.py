from __future__ import annotations

import base64
import json
from urllib.parse import parse_qs, urlparse

import pytest

from app.config import Settings
from app.services.entra_auth_service import EntraAuthService


def _make_settings(authority_url: str) -> Settings:
    return Settings(
        app_env="test",
        web_app_port=8000,
        azure_tenant_id="tenant-test",
        azure_client_id="client-test",
        azure_client_secret="secret-test",
        oidc_authority_url=authority_url,
        oidc_callback_url_test="http://localhost:8000/auth/callback",
        oidc_callback_url_prod="https://example.azurewebsites.net/auth/callback",
        sql_server="server.database.windows.net",
        sql_database="db",
        openai_endpoint="https://example.openai.azure.com",
        openai_api_version="2024-10-21",
        openai_deployment="gpt-4o-mini",
        google_news_rss_base_url="https://news.google.com/rss/search",
        sql_max_rows=100,
        mock_auth_enabled=False,
    )


def _encode_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode("utf-8")).decode("utf-8")
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return f"{header.rstrip('=')}.{payload.rstrip('=')}.sig"


@pytest.mark.parametrize(
    "authority_url",
    [
        "https://login.microsoftonline.com/tenant-test",
        "https://login.microsoftonline.com/tenant-test/",
        "https://login.microsoftonline.com/tenant-test/v2.0",
        "https://login.microsoftonline.com/tenant-test/v2.0/",
        "https://login.microsoftonline.com/tenant-test/oauth2/v2.0",
        "https://login.microsoftonline.com/tenant-test/oauth2/v2.0/",
    ],
)
def test_login_redirect_url_normalizes_authority(authority_url: str):
    service = EntraAuthService(_make_settings(authority_url), {})
    url = service.login_redirect_url()
    parsed = urlparse(url)

    assert parsed.path == "/tenant-test/oauth2/v2.0/authorize"
    query = parse_qs(parsed.query)
    assert query["client_id"] == ["client-test"]
    assert query["redirect_uri"] == ["http://localhost:8000/auth/callback"]
    assert query["response_type"] == ["code"]
    assert query["response_mode"] == ["query"]
    assert query["scope"] == ["openid profile email"]
    assert query["state"][0]


@pytest.mark.parametrize(
    "authority_url",
    [
        "https://login.microsoftonline.com/tenant-test/v2.0",
        "https://login.microsoftonline.com/tenant-test/oauth2/v2.0",
    ],
)
def test_process_callback_uses_normalized_token_endpoint(
    authority_url: str, monkeypatch: pytest.MonkeyPatch
):
    captured: dict[str, str] = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "id_token": _encode_jwt(
                    {
                        "tid": "tenant-test",
                        "oid": "oid-123",
                        "name": "Tester",
                        "preferred_username": "tester@example.com",
                    }
                )
            }

    def fake_post(url: str, data: dict, timeout: float):
        captured["url"] = url
        return FakeResponse()

    monkeypatch.setattr("app.services.entra_auth_service.httpx.post", fake_post)

    service = EntraAuthService(_make_settings(authority_url), {})
    user = service.process_callback(code="auth-code")

    assert captured["url"] == "https://login.microsoftonline.com/tenant-test/oauth2/v2.0/token"
    assert user["tenant_id"] == "tenant-test"
    assert user["user_id"] == "oid-123"
