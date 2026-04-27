from __future__ import annotations

import pytest

from app.config import Settings
from app.data.repositories.customer_repository import CustomerRepository
from app.errors import AppError


class FakeSqlClient:
    def __init__(self, rows=None, query_handler=None):  # noqa: ANN001
        self.last_sql: str | None = None
        self.queries: list[str] = []
        self._rows = [] if rows is None else rows
        self._query_handler = query_handler

    def query(self, sql: str, params=(), **_kwargs):  # noqa: ANN001
        self.last_sql = sql
        self.queries.append(sql)
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
        db_read_governance_enabled=True,
        queryvisibility_api_url="https://purview.example.test/query",
        queryvisibility_openapi_url="https://purview.example.test/query/openapi.json",
        queryvisibility_openapi_path="/query",
        mask_api_url="https://purview.example.test/mask",
        mask_openapi_url="https://purview.example.test/mask/openapi.json",
        mask_openapi_path="/mask",
    )


def test_query_customers_injects_top_without_subquery_for_order_by():
    fake_sql_client = FakeSqlClient()
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=100))

    repo.query_customers(
        "SELECT CustomerID, CompanyName FROM SalesLT.Customer ORDER BY CustomerID DESC;"
    )

    assert fake_sql_client.last_sql is not None
    assert fake_sql_client.last_sql.startswith("SELECT TOP 4 CustomerID, CompanyName")
    assert "FROM (" not in fake_sql_client.last_sql
    assert fake_sql_client.last_sql.endswith("ORDER BY CustomerID DESC")


def test_query_customers_injects_top_after_distinct():
    fake_sql_client = FakeSqlClient()
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=25))

    repo.query_customers("SELECT DISTINCT CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC")

    assert fake_sql_client.last_sql == "SELECT DISTINCT TOP 4 CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC"


def test_query_customers_caps_existing_top():
    fake_sql_client = FakeSqlClient()
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=50))

    repo.query_customers("SELECT TOP 10 CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC")

    assert fake_sql_client.last_sql == "SELECT TOP 4 CustomerID FROM SalesLT.Customer ORDER BY CustomerID DESC"


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
    assert any("CompanyName AS company_name" in sql for sql in fake_sql_client.queries)


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
            "addresses": [],
            "address_display": None,
            "relevance_score": 1.0,
            "match_reason": None,
            "order_count": 0,
            "lifetime_value": 0.0,
        }
    ]


def test_query_customers_caps_response_size_to_four():
    rows = [{"CustomerID": idx, "CompanyName": f"Company-{idx}"} for idx in range(1, 26)]
    fake_sql_client = FakeSqlClient(rows=rows)
    repo = CustomerRepository(fake_sql_client, _make_settings(sql_max_rows=100))

    results = repo.query_customers("SELECT CustomerID, CompanyName FROM SalesLT.Customer ORDER BY CustomerID")

    assert len(results) == 4
    assert [item["customer_id"] for item in results] == list(range(1, 5))


def test_query_customers_raises_when_required_identity_columns_missing():
    fake_sql_client = FakeSqlClient(rows=[{"TotalOrderAmount": 12.3}])
    repo = CustomerRepository(fake_sql_client, _make_settings())

    with pytest.raises(AppError) as exc:
        repo.query_customers("SELECT SUM(TotalDue) AS TotalOrderAmount FROM SalesLT.SalesOrderHeader")

    assert exc.value.status_code == 400


def test_get_customer_order_line_items_selects_required_columns_only():
    fake_sql_client = FakeSqlClient(rows=[])
    repo = CustomerRepository(fake_sql_client, _make_settings())

    repo.get_customer_order_line_items(1, user_principal_name="user@example.com")

    assert fake_sql_client.last_sql is not None
    assert "SELECT TOP 4" in fake_sql_client.last_sql
    select_clause = fake_sql_client.last_sql.split("FROM SalesLT.SalesOrderHeader", 1)[0]
    assert "sod.OrderQty AS order_qty" in select_clause
    assert "sod.UnitPrice AS unit_price" in select_clause
    assert "sod.UnitPriceDiscount AS unit_price_discount" in select_clause
    assert "soh.OrderDate AS order_date" in select_clause
    assert "soh.SubTotal AS sub_total" in select_clause
    assert "p.Name AS product_name" in select_clause
    assert "sod.LineTotal" not in select_clause
    assert "soh.ShipDate" not in select_clause
    assert "soh.TaxAmt" not in select_clause
    assert "soh.TotalDue" not in select_clause
    assert "soh.Freight" not in select_clause


def test_get_customer_order_line_items_limits_mock_rows_to_four(monkeypatch):
    from app.data.repositories import customer_repository

    monkeypatch.setitem(
        customer_repository.ORDERS,
        1,
        [
            {"order_id": 1, "order_date": "2026-01-01", "total_due": 1.0},
            {"order_id": 2, "order_date": "2026-01-02", "total_due": 2.0},
            {"order_id": 3, "order_date": "2026-01-03", "total_due": 3.0},
            {"order_id": 4, "order_date": "2026-01-04", "total_due": 4.0},
            {"order_id": 5, "order_date": "2026-01-05", "total_due": 5.0},
        ],
    )
    repo = CustomerRepository(None, _make_settings())

    rows = repo.get_customer_order_line_items(1, user_principal_name="user@example.com")

    assert len(rows) == 4


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
