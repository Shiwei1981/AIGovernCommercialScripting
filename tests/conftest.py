from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


def _set_test_env() -> None:
    os.environ.update(
        {
            "APP_ENV": "test",
            "WEB_APP_PORT": "8000",
            "AZURE_TENANT_ID": "tenant-test",
            "AZURE_CLIENT_ID": "client-test",
            "AZURE_CLIENT_SECRET": "secret-test",
            "OIDC_AUTHORITY_URL": "https://login.microsoftonline.com/tenant-test/v2.0",
            "OIDC_CALLBACK_URL_TEST": "http://localhost:8000/auth/callback",
            "OIDC_CALLBACK_URL_PROD": "https://example.azurewebsites.net/auth/callback",
            "SQL_SERVER": "server.database.windows.net",
            "SQL_DATABASE": "db",
            "OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "OPENAI_API_VERSION": "2024-10-21",
            "OPENAI_DEPLOYMENT": "gpt-4o-mini",
            "GOOGLE_NEWS_RSS_BASE_URL": "https://news.google.com/rss/search",
            "SQL_MAX_ROWS": "100",
            "MOCK_AUTH_ENABLED": "true",
            "DB_READ_GOVERNANCE_ENABLED": "true",
            "QUERYVISIBILITY_API_URL": "https://purview.example.test/query",
            "QUERYVISIBILITY_OPENAPI_URL": "https://purview.example.test/query/openapi.json",
            "QUERYVISIBILITY_OPENAPI_PATH": "/query",
            "MASK_API_URL": "https://purview.example.test/mask",
            "MASK_OPENAPI_URL": "https://purview.example.test/mask/openapi.json",
            "MASK_OPENAPI_PATH": "/mask",
        }
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _set_test_env()
    from app.main import create_app

    monkeypatch.setattr(
        "app.services.nl2sql_service.invoke_model",
        lambda *_: (
            "SELECT CustomerID AS customer_id, CompanyName AS customer_name, "
            "1.0 AS relevance_score FROM Customer"
        ),
    )
    monkeypatch.setattr(
        "app.services.customer_analysis_service.invoke_model",
        lambda *_: "Customer has strong growth potential.",
    )
    monkeypatch.setattr(
        "app.services.ad_copy_service.invoke_model",
        lambda *_: "Ad copy generated for selected customer and product.",
    )
    def fake_news_model(_settings, prompt):  # noqa: ANN001
        if "Generate one broad Google News search query" in prompt:
            return "demo product market demand"
        return "Trend summary with citations [1][2]."

    monkeypatch.setattr("app.services.news_trend_service.invoke_model", fake_news_model)

    def fake_parse(_url):
        entries = [
            {
                "title": "News A",
                "link": "https://news.google.com/articles/abc?url=https://publisher/a",
                "published": "Sat, 07 Mar 2026 08:00:00 GMT",
                "summary": "<a href='https://publisher/a'>News A</a><font>Publisher A</font><p>Demand is improving for this product segment.</p>",
                "source": {"title": "Publisher A", "href": "https://publisher/a"},
            },
            {
                "title": "News B",
                "link": "https://news.google.com/articles/def?url=https://publisher/b",
                "published": "Sun, 08 Mar 2026 09:00:00 GMT",
                "summary": "<a href='https://publisher/b'>News B</a><font>Publisher B</font><p>Retail interest and launches remain active.</p>",
                "source": {"title": "Publisher B", "href": "https://publisher/b"},
            },
        ]
        return SimpleNamespace(entries=entries, bozo=False)

    monkeypatch.setattr("app.services.news_trend_service.feedparser.parse", fake_parse)

    app = create_app()
    return TestClient(app)


@pytest.fixture()
def auth_client(client: TestClient) -> TestClient:
    client.get("/auth/callback?mock_user=tester", allow_redirects=False)
    return client
