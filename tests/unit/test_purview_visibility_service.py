from __future__ import annotations

from types import SimpleNamespace

import httpx

from app.services.purview_visibility_service import PurviewVisibilityService


def _service() -> PurviewVisibilityService:
    return PurviewVisibilityService(
        SimpleNamespace(
            queryvisibility_api_url="https://purview.example.test/query",
            mask_api_url="https://purview.example.test/mask",
        )
    )


def test_query_visibility_skips_api_when_qualified_name_ends_with_id(monkeypatch):
    def fail_post(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("QueryVisibility API should not be called for ID resources")

    monkeypatch.setattr("app.services.purview_visibility_service.httpx.post", fail_post)

    decision = _service().query_visibility(
        resource_type="column",
        qualified_name="mssql://server.database.windows.net/db/SalesLT/Customer#CustomerID",
        user_principal_name="user@example.com",
    )

    assert decision.result == "NOT_APPLICABLE"


def test_query_visibility_calls_api_for_non_id_resources(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):  # noqa: ANN001
        calls.append((url, json, timeout))
        return httpx.Response(200, json={"result": "ALLOW"}, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.services.purview_visibility_service.httpx.post", fake_post)

    decision = _service().query_visibility(
        resource_type="column",
        qualified_name="mssql://server.database.windows.net/db/SalesLT/Customer#CompanyName",
        user_principal_name="user@example.com",
    )

    assert decision.result == "ALLOW"
    assert calls == [
        (
            "https://purview.example.test/query",
            {
                "QualifiedName": "mssql://server.database.windows.net/db/SalesLT/Customer#CompanyName",
                "UserPrincipalName": "user@example.com",
            },
            10.0,
        )
    ]
