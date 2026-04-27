from __future__ import annotations

import pytest

from app.config import Settings
from app.errors import AppError
from app.services.sql_resource_parser import (
    SQL_RESOURCE_PARSE_ERROR,
    SQLResourceParser,
    build_qualified_name,
)


def _settings() -> Settings:
    return Settings(
        app_env="test",
        web_app_port=8000,
        azure_tenant_id="tenant-test",
        azure_client_id="client-test",
        azure_client_secret="secret-test",
        oidc_authority_url="https://login.microsoftonline.com/tenant-test/v2.0",
        oidc_callback_url_test="http://localhost:8000/auth/callback",
        oidc_callback_url_prod="https://example.azurewebsites.net/auth/callback",
        sql_server="server",
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
    )


def _parser() -> SQLResourceParser:
    columns = {
        ("saleslt", "customer"): ["CustomerID", "CompanyName", "FirstName", "LastName"],
        ("saleslt", "customeraddress"): ["CustomerID", "AddressID"],
        ("saleslt", "address"): ["AddressID", "City", "PostalCode"],
        ("saleslt", "product"): ["ProductID", "Name", "ProductCategoryID"],
        ("saleslt", "productcategory"): ["ProductCategoryID", "Name"],
    }
    return SQLResourceParser(_settings(), lambda schema, table: columns.get((schema.lower(), table.lower()), []))


def test_parser_resolves_join_aliases_and_expression_inputs():
    resources = _parser().parse(
        "SELECT c.CustomerID AS customer_id, UPPER(a.City) AS city "
        "FROM SalesLT.Customer c "
        "JOIN SalesLT.CustomerAddress ca ON c.CustomerID = ca.CustomerID "
        "JOIN SalesLT.Address a ON ca.AddressID = a.AddressID "
        "ORDER BY city"
    )

    table_names = {item.table_name for item in resources.tables}
    column_names = {(item.table_name, item.column_name) for item in resources.columns}
    assert table_names == {"Customer", "CustomerAddress", "Address"}
    assert ("Customer", "CustomerID") in column_names
    assert ("Address", "City") in column_names
    assert ("CustomerAddress", "AddressID") in column_names


def test_parser_expands_star_from_metadata():
    resources = _parser().parse("SELECT c.* FROM SalesLT.Customer c")

    assert {item.column_name for item in resources.columns} == {
        "CustomerID",
        "CompanyName",
        "FirstName",
        "LastName",
    }
    assert resources.result_column_sources["companyname"] == [
        "mssql://server.database.windows.net/db/SalesLT/Customer#CompanyName"
    ]


def test_parser_normalizes_bracketed_table_identifiers_for_qualified_names():
    resources = _parser().parse(
        "SELECT c.CompanyName AS company_name FROM [SalesLT.Customer] c"
    )

    assert [table.qualified_name for table in resources.tables] == [
        "mssql://server.database.windows.net/db/SalesLT/Customer"
    ]
    assert resources.result_column_sources["companyname"] == [
        "mssql://server.database.windows.net/db/SalesLT/Customer#CompanyName"
    ]


def test_parser_uses_slash_for_table_and_hash_for_column_qualified_names():
    resources = _parser().parse(
        "SELECT p.ProductID AS product_id, pc.Name AS category_name "
        "FROM SalesLT.Product p "
        "JOIN SalesLT.ProductCategory pc ON p.ProductCategoryID = pc.ProductCategoryID"
    )

    assert {table.qualified_name for table in resources.tables} == {
        "mssql://server.database.windows.net/db/SalesLT/Product",
        "mssql://server.database.windows.net/db/SalesLT/ProductCategory",
    }
    assert "mssql://server.database.windows.net/db/SalesLT/Product#ProductID" in {
        column.qualified_name for column in resources.columns
    }
    assert "mssql://server.database.windows.net/db/SalesLT/ProductCategory#Name" in {
        column.qualified_name for column in resources.columns
    }


def test_build_qualified_name_does_not_duplicate_fqdn_suffix_and_uses_hash_for_columns():
    settings = _settings()
    settings = Settings(**{**settings.__dict__, "sql_server": "server.database.windows.net"})

    assert (
        build_qualified_name(settings, "SalesLT", "Customer")
        == "mssql://server.database.windows.net/db/SalesLT/Customer"
    )
    assert (
        build_qualified_name(settings, "SalesLT", "Customer", "CompanyName")
        == "mssql://server.database.windows.net/db/SalesLT/Customer#CompanyName"
    )


def test_parser_rejects_non_read_only_sql():
    with pytest.raises(AppError) as exc:
        _parser().parse("DELETE FROM SalesLT.Customer")

    assert exc.value.status_code == 400


def test_parser_fails_closed_when_resource_unresolved():
    with pytest.raises(AppError) as exc:
        _parser().parse("SELECT MissingColumn FROM SalesLT.Customer c JOIN SalesLT.Address a ON 1 = 1")

    assert exc.value.status_code == 422
    assert exc.value.message == SQL_RESOURCE_PARSE_ERROR
