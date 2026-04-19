from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    web_app_port: int
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    oidc_authority_url: str
    oidc_callback_url_test: str
    oidc_callback_url_prod: str
    sql_server: str
    sql_database: str
    openai_endpoint: str
    openai_api_version: str
    openai_deployment: str
    google_news_rss_base_url: str
    sql_max_rows: int
    mock_auth_enabled: bool

    @property
    def is_test(self) -> bool:
        return self.app_env.lower() == "test"

    @property
    def oidc_callback_url(self) -> str:
        if self.app_env.lower() in {"prod", "production"}:
            return self.oidc_callback_url_prod
        return self.oidc_callback_url_test


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _as_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "dev").strip() or "dev"
    settings = Settings(
        app_env=app_env,
        web_app_port=int(os.getenv("WEB_APP_PORT", "8000")),
        azure_tenant_id=_required("AZURE_TENANT_ID"),
        azure_client_id=_required("AZURE_CLIENT_ID"),
        azure_client_secret=_required("AZURE_CLIENT_SECRET"),
        oidc_authority_url=_required("OIDC_AUTHORITY_URL"),
        oidc_callback_url_test=_required("OIDC_CALLBACK_URL_TEST"),
        oidc_callback_url_prod=_required("OIDC_CALLBACK_URL_PROD"),
        sql_server=_required("SQL_SERVER"),
        sql_database=_required("SQL_DATABASE"),
        openai_endpoint=_required("OPENAI_ENDPOINT"),
        openai_api_version=_required("OPENAI_API_VERSION"),
        openai_deployment=_required("OPENAI_DEPLOYMENT"),
        google_news_rss_base_url=_required("GOOGLE_NEWS_RSS_BASE_URL"),
        sql_max_rows=int(os.getenv("SQL_MAX_ROWS", "100")),
        mock_auth_enabled=_as_bool("MOCK_AUTH_ENABLED", False),
    )
    if settings.mock_auth_enabled and not settings.is_test:
        raise RuntimeError("MOCK_AUTH_ENABLED can only be true when APP_ENV=test")
    return settings
