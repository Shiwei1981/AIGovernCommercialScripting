from __future__ import annotations

import logging
import os
from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from app import telemetry
from app.config import Settings


def _make_settings(
    *,
    connection_string: str | None = "InstrumentationKey=test-key",
    otel_service_name: str | None = None,
) -> Settings:
    return Settings(
        app_env="test",
        web_app_port=8000,
        azure_tenant_id="tenant-test",
        azure_client_id="client-test",
        azure_client_secret="secret-test",
        oidc_authority_url="https://login.microsoftonline.com/tenant-test/v2.0",
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
        db_read_governance_enabled=True,
        queryvisibility_api_url="https://purview.example.test/query",
        queryvisibility_openapi_url="https://purview.example.test/query/openapi.json",
        queryvisibility_openapi_path="/query",
        mask_api_url="https://purview.example.test/mask",
        mask_openapi_url="https://purview.example.test/mask/openapi.json",
        mask_openapi_path="/mask",
        applicationinsights_connection_string=connection_string,
        otel_service_name=otel_service_name,
    )


@pytest.fixture(autouse=True)
def reset_telemetry_state(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(telemetry, "_TELEMETRY_CONFIGURED", False)
    monkeypatch.setattr(telemetry, "_HTTPX_INSTRUMENTED", False)
    monkeypatch.setattr(telemetry, "_FASTAPI_INSTRUMENTED", set())
    monkeypatch.setattr(telemetry, "_TELEMETRY_IMPORTS_LOADED", False)
    monkeypatch.setattr(telemetry, "_CONFIGURE_AZURE_MONITOR", None)
    monkeypatch.setattr(telemetry, "_FASTAPI_INSTRUMENTOR", None)
    monkeypatch.setattr(telemetry, "_HTTPX_CLIENT_INSTRUMENTOR", None)
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)


def test_configure_telemetry_skips_when_connection_string_missing(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO)
    telemetry.configure_telemetry(_make_settings(connection_string=None))

    assert not telemetry._TELEMETRY_CONFIGURED
    assert "Application Insights disabled" in caplog.text


def test_configure_telemetry_handles_missing_optional_dependencies(monkeypatch: pytest.MonkeyPatch):
    def fake_import_module(name: str):
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr(telemetry.importlib, "import_module", fake_import_module)

    telemetry.configure_telemetry(_make_settings())

    assert not telemetry._TELEMETRY_CONFIGURED


def test_configure_telemetry_enables_monitoring_and_instruments_app(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    class FakeHTTPXClientInstrumentor:
        def instrument(self) -> None:
            captured["httpx_instrumented"] = True

    class FakeFastAPIInstrumentor:
        @staticmethod
        def instrument_app(app: FastAPI) -> None:
            captured["instrumented_app"] = app

    def fake_configure_azure_monitor(**kwargs) -> None:
        captured["configure_kwargs"] = kwargs

    def fake_import_module(name: str):
        mapping = {
            "azure.monitor.opentelemetry": SimpleNamespace(
                configure_azure_monitor=fake_configure_azure_monitor
            ),
            "opentelemetry.instrumentation.fastapi": SimpleNamespace(
                FastAPIInstrumentor=FakeFastAPIInstrumentor
            ),
            "opentelemetry.instrumentation.httpx": SimpleNamespace(
                HTTPXClientInstrumentor=FakeHTTPXClientInstrumentor
            ),
        }
        return mapping[name]

    monkeypatch.setattr(telemetry.importlib, "import_module", fake_import_module)

    app = FastAPI()
    telemetry.configure_telemetry(_make_settings())
    telemetry.instrument_app(app)

    assert telemetry._TELEMETRY_CONFIGURED
    assert telemetry._HTTPX_INSTRUMENTED
    assert captured["configure_kwargs"] == {
        "connection_string": "InstrumentationKey=test-key",
        "logger_name": "ai-commercial-assistant",
        "instrumentation_options": telemetry._instrumentation_options(),
    }
    assert captured["httpx_instrumented"] is True
    assert captured["instrumented_app"] is app
    assert os.environ["OTEL_SERVICE_NAME"] == "ai-commercial-assistant"


def test_configure_telemetry_prefers_explicit_service_name(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    class FakeHTTPXClientInstrumentor:
        def instrument(self) -> None:
            captured["httpx_instrumented"] = True

    def fake_import_module(name: str):
        mapping = {
            "azure.monitor.opentelemetry": SimpleNamespace(
                configure_azure_monitor=lambda **kwargs: captured.setdefault("kwargs", kwargs)
            ),
            "opentelemetry.instrumentation.fastapi": SimpleNamespace(
                FastAPIInstrumentor=type(
                    "FakeFastAPIInstrumentor",
                    (),
                    {"instrument_app": staticmethod(lambda app: None)},
                )
            ),
            "opentelemetry.instrumentation.httpx": SimpleNamespace(
                HTTPXClientInstrumentor=FakeHTTPXClientInstrumentor
            ),
        }
        return mapping[name]

    monkeypatch.setattr(telemetry.importlib, "import_module", fake_import_module)

    telemetry.configure_telemetry(
        _make_settings(otel_service_name="CommercialScriptingWithPurview")
    )

    assert os.environ["OTEL_SERVICE_NAME"] == "CommercialScriptingWithPurview"
