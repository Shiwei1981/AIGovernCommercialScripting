from __future__ import annotations

import importlib
import logging
import os
from typing import Any

from fastapi import FastAPI

from app.config import Settings

LOGGER = logging.getLogger(__name__)

_TELEMETRY_CONFIGURED = False
_HTTPX_INSTRUMENTED = False
_FASTAPI_INSTRUMENTED: set[int] = set()
_TELEMETRY_IMPORTS_LOADED = False
_CONFIGURE_AZURE_MONITOR = None
_FASTAPI_INSTRUMENTOR = None
_HTTPX_CLIENT_INSTRUMENTOR = None


def configure_telemetry(settings: Settings) -> None:
    global _TELEMETRY_CONFIGURED, _HTTPX_INSTRUMENTED

    if _TELEMETRY_CONFIGURED:
        return

    if not settings.applicationinsights_connection_string:
        LOGGER.info("Application Insights disabled because APPLICATIONINSIGHTS_CONNECTION_STRING is not set.")
        return

    if not _load_telemetry_dependencies():
        LOGGER.warning(
            "Application Insights requested but telemetry dependencies are not installed."
        )
        return

    service_name = settings.otel_service_name or os.getenv("OTEL_SERVICE_NAME") or "ai-commercial-assistant"
    if not os.getenv("OTEL_SERVICE_NAME"):
        os.environ["OTEL_SERVICE_NAME"] = service_name

    _CONFIGURE_AZURE_MONITOR(
        connection_string=settings.applicationinsights_connection_string,
        logger_name="ai-commercial-assistant",
        instrumentation_options=_instrumentation_options(),
    )
    if not _HTTPX_INSTRUMENTED:
        _HTTPX_CLIENT_INSTRUMENTOR().instrument()
        _HTTPX_INSTRUMENTED = True
    _TELEMETRY_CONFIGURED = True
    LOGGER.info("Application Insights enabled with OTEL service name '%s'.", service_name)


def instrument_app(app: FastAPI) -> None:
    if not _TELEMETRY_CONFIGURED:
        return
    app_identity = id(app)
    if app_identity in _FASTAPI_INSTRUMENTED:
        return
    _FASTAPI_INSTRUMENTOR.instrument_app(app)
    _FASTAPI_INSTRUMENTED.add(app_identity)


def _load_telemetry_dependencies() -> bool:
    global _TELEMETRY_IMPORTS_LOADED
    global _CONFIGURE_AZURE_MONITOR, _FASTAPI_INSTRUMENTOR, _HTTPX_CLIENT_INSTRUMENTOR

    if _TELEMETRY_IMPORTS_LOADED:
        return True

    try:
        azure_monitor_module = importlib.import_module("azure.monitor.opentelemetry")
        fastapi_module = importlib.import_module("opentelemetry.instrumentation.fastapi")
        httpx_module = importlib.import_module("opentelemetry.instrumentation.httpx")
    except ModuleNotFoundError as exc:
        LOGGER.warning("Application Insights dependency import failed: %s", exc.name)
        return False

    _CONFIGURE_AZURE_MONITOR = azure_monitor_module.configure_azure_monitor
    _FASTAPI_INSTRUMENTOR = fastapi_module.FastAPIInstrumentor
    _HTTPX_CLIENT_INSTRUMENTOR = httpx_module.HTTPXClientInstrumentor
    _TELEMETRY_IMPORTS_LOADED = True
    return True


def _instrumentation_options() -> dict[str, dict[str, Any]]:
    return {
        "azure_sdk": {"enabled": True},
        "fastapi": {"enabled": False},
        "requests": {"enabled": True},
        "urllib": {"enabled": True},
        "urllib3": {"enabled": True},
    }
