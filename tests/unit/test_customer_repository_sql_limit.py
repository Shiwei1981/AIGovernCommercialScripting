from __future__ import annotations

import pytest

from app.config import Settings
from app.data.repositories.customer_repository import CustomerRepository
from app.errors import AppError


class FakeSqlClient:
    def __init__(self, rows=None, query_handler=None):  # noqa: ANN001
        self.last_sql: str | None = None
        self._rows = [] if rows is None else rows
        self._query_handler = query_handler

    def query(self, sql: str, params=()):  # noqa: ANN001
        self.last_sql = sql
        if self._query_handler is not None:
            return self._query_handler(sql, params)
        return self._rows


def _make_settings(sql_max_rows: int = 100) -> Settings:
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
        sql_max_rows=sql_max_rows,
        mock_auth_enabled=False,
    )


def test_query_customers_injects_top_without_subquery_for_order_by():
    fake_sql_client = FakeSqlClient()
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=100))

    repo.query_customers(
        "SELECT CustomerID, CompanyName FROM SalesLT.Customer ORDER BY CustomerID DESC;"
    )

    assert fake_sql_client.last_sql is not None
    assert fake_sql_client.last_sql.startswith("SELECT TOP 10 CustomerID, CompanyName")
    assert "FROM (" not in fake_sql_client.last_sql
    assert fake_sql_client.last_sql.endswith("ORDER BY CustomerID DESC")


def test_query_customers_injects_top_after_distinct():
    fake_sql_client = FakeSqlClient()
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=25))

    repo.query_customers("SELECT DISTINCT CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC")

    assert fake_sql_client.last_sql == "SELECT DISTINCT TOP 10 CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC"


def test_query_customers_keeps_existing_top():
    fake_sql_client = FakeSqlClient()
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=50))

    repo.query_customers("SELECT TOP 10 CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC")

    assert fake_sql_client.last_sql == "SELECT TOP 10 CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC"


def test_query_customers_normalizes_common_column_names():
    fake_sql_client = FakeSqlClient(
        rows=[
            {
                "CustomerID": 29736,
                "FirstName": "Terry",
                "LastName": "Eminhizer",
                "TotalOrderAmount": 119960.8240,
            }
        ]
    )
    repo = CustomerRepository(fake_sql_client, _make_settings())

    results = repo.query_customers(
        "SELECT CustomerID, FirstName, LastName, SUM(TotalDue) AS TotalOrderAmount "
        "FROM SalesLT.Customer c JOIN SalesLT.SalesOrderHeader h ON c.CustomerID = h.CustomerID "
        "GROUP BY CustomerID, FirstName, LastName ORDER BY TotalOrderAmount DESC"
    )

    assert len(results) == 1
    assert results[0]["customer_id"] == 29736
    assert results[0]["customer_name"] == "Terry Eminhizer"
    assert results[0]["relevance_score"] == pytest.approx(119960.8240)
    assert results[0]["lifetime_value"] == pytest.approx(119960.8240)


def test_query_customers_uses_fallback_relevance_when_score_missing():
    fake_sql_client = FakeSqlClient(rows=[{"CustomerID": 1, "CompanyName": "Contoso"}])
    repo = CustomerRepository(fake_sql_client, _make_settings())

    results = repo.query_customers("SELECT CustomerID, CompanyName FROM SalesLT.Customer")

    assert results == [
        {
            "customer_id": 1,
            "customer_name": "Contoso",
            "company_name": "Contoso",
            "location": None,
            "relevance_score": 1.0,
            "match_reason": None,
            "order_count": 0,
            "lifetime_value": 0.0,
        }
    ]


def test_query_customers_caps_response_size_to_ten():
    rows = [{"CustomerID": idx, "CompanyName": f"Company-{idx}"} for idx in range(1, 26)]
    fake_sql_client = FakeSqlClient(rows=rows)
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=100))

    results = repo.query_customers("SELECT CustomerID, CompanyName FROM SalesLT.Customer ORDER BY CustomerID")

    assert len(results) == 10
    assert [item["customer_id"] for item in results] == list(range(1, 11))


def test_query_customers_raises_when_required_identity_columns_missing():
    fake_sql_client = FakeSqlClient(rows=[{"TotalOrderAmount": 12.3}])
    repo = CustomerRepository(fake_sql_client, _make_settings())

    with pytest.raises(AppError) as exc:
        repo.query_customers("SELECT SUM(TotalDue) AS TotalOrderAmount FROM SalesLT.SalesOrderHeader")

    assert exc.value.status_code == 400


def test_get_order_history_returns_empty_history_for_existing_customer_without_orders():
    def _query_handler(sql: str, params: tuple[int, ...]):  # noqa: ARG001
        if "FROM SalesLT.SalesOrderHeader" in sql:
            return []
        if "FROM SalesLT.Customer WHERE CustomerID = ?" in sql:
            return [{"customer_id": 29605}]
        return []

    fake_sql_client = FakeSqlClient(query_handler=_query_handler)
    repo = CustomerRepository(fake_sql_client, _make_settings())

    history = repo.get_order_history(29605)

    assert history == {
        "customer_id": 29605,
        "total_orders": 0,
        "total_amount": 0.0,
        "last_order_date": None,
        "orders": [],
    }


def test_get_order_history_raises_not_found_when_customer_missing():
    def _query_handler(sql: str, params: tuple[int, ...]):  # noqa: ARG001
        if "FROM SalesLT.SalesOrderHeader" in sql:
            return []
        if "FROM SalesLT.Customer WHERE CustomerID = ?" in sql:
            return []
        return []

    fake_sql_client = FakeSqlClient(query_handler=_query_handler)
    repo = CustomerRepository(fake_sql_client, _make_settings())

    with pytest.raises(AppError) as exc:
        repo.get_order_history(999999)

    assert exc.value.status_code == 404
