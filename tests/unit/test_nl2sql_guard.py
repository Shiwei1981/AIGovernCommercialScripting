from types import SimpleNamespace

import pytest

from app.errors import AppError
from app.services.nl2sql_service import NL2SQLService, qualify_saleslt_schema, validate_select_only


def test_guard_allows_select():
    validate_select_only("SELECT * FROM Customer")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM Customer",
        "UPDATE Customer SET Name='x'",
        "MERGE Customer AS target USING Other AS source ON 1 = 1 WHEN MATCHED THEN UPDATE SET Name='x'",
        "CREATE VIEW v AS SELECT 1 AS x",
        "SELECT * FROM C; DROP TABLE X",
    ],
)
def test_guard_rejects_non_readonly(sql):
    with pytest.raises(AppError):
        validate_select_only(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT c.CustomerID AS customer_id FROM Customer c",
        "SELECT c.CustomerID AS customer_id FROM [Customer] c",
        "SELECT c.CustomerID AS customer_id FROM SalesLT.[Customer] c",
        "SELECT c.CustomerID AS customer_id FROM [SalesLT].[Customer] c",
        "SELECT c.CustomerID AS customer_id FROM [SalesLT.Customer] c",
    ],
)
def test_qualify_saleslt_schema_normalizes_customer_table_references(sql):
    qualified = qualify_saleslt_schema(sql)

    assert "FROM SalesLT.Customer AS c" in qualified
    assert "SalesLT.Customer]" not in qualified
    assert "[SalesLT].[SalesLT.Customer]" not in qualified


def test_generate_sql_prompt_requires_company_name(monkeypatch):
    captured = {}

    def fake_model(_settings, prompt):  # noqa: ANN001
        captured["prompt"] = prompt
        return "SELECT CustomerID AS customer_id, CompanyName AS company_name FROM Customer"

    monkeypatch.setattr("app.services.nl2sql_service.invoke_model", fake_model)
    service = NL2SQLService(
        SimpleNamespace(openai_deployment="gpt"),
        SimpleNamespace(
            call_with_logging=lambda **kwargs: kwargs["callback"](),
        ),
    )

    service.generate_sql("high value", user_identity="user@example.com")

    assert "customer_id, customer_name, company_name, relevance_score" in captured["prompt"]
    assert "Do not return location, match_reason, order_count, lifetime_value" in captured["prompt"]
    assert "Optional aliases:" not in captured["prompt"]
