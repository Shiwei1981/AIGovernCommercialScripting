from __future__ import annotations

import pytest

from app.errors import AppError
from app.services.db_read_governance_service import DBReadGovernanceService
from app.services.purview_visibility_service import VisibilityDecision
from app.services.sql_resource_parser import SQLColumnResource, SQLReadResourceSet, SQLTableResource


class FakeParser:
    def parse(self, _sql):  # noqa: ANN001
        table = SQLTableResource("SalesLT", "Customer", "mssql://server.database.windows.net/db/SalesLT/Customer")
        column = SQLColumnResource(
            "SalesLT",
            "Customer",
            "CompanyName",
            "mssql://server.database.windows.net/db/SalesLT/Customer#CompanyName",
        )
        return SQLReadResourceSet(
            tables=[table],
            columns=[column],
            result_column_sources={"companyname": [column.qualified_name]},
        )


class FakePurview:
    def __init__(self, table_result: str = "ALLOW", column_result: str = "ALLOW") -> None:
        self.table_result = table_result
        self.column_result = column_result
        self.mask_calls: list[tuple[str, str]] = []

    def query_visibility(self, *, resource_type, qualified_name, user_principal_name):  # noqa: ANN001
        result = self.table_result if resource_type == "table" else self.column_result
        return VisibilityDecision(resource_type, qualified_name, result)

    def mask(self, *, qualified_name, mask_input):  # noqa: ANN001
        self.mask_calls.append((qualified_name, str(mask_input)))
        return f"masked:{mask_input}"


def test_authorize_allows_non_deny_decisions():
    service = DBReadGovernanceService(FakeParser(), FakePurview(table_result="INDETERMINATE"))

    _, decisions = service.authorize("SELECT CompanyName FROM SalesLT.Customer", "user@example.com")

    assert [decision.result for decision in decisions] == ["INDETERMINATE", "ALLOW"]


def test_authorize_blocks_deny():
    service = DBReadGovernanceService(FakeParser(), FakePurview(column_result="DENY"))

    with pytest.raises(AppError) as exc:
        service.authorize("SELECT CompanyName FROM SalesLT.Customer", "user@example.com")

    assert "Current user is not allowed to read data:" in exc.value.message
    assert exc.value.status_code == 403


def test_column_mask_replaces_matching_result_cells():
    purview = FakePurview(column_result="MASK")
    service = DBReadGovernanceService(FakeParser(), purview)
    resources, decisions = service.authorize("SELECT CompanyName FROM SalesLT.Customer", "user@example.com")

    rows = service.apply_masks([{"CustomerID": 1, "CompanyName": "Contoso"}], resources, decisions)

    assert rows[0]["CustomerID"] == 1
    assert rows[0]["CompanyName"] == "masked:Contoso"


def test_table_mask_skips_id_like_columns():
    purview = FakePurview(table_result="MASK")
    service = DBReadGovernanceService(FakeParser(), purview)
    resources, decisions = service.authorize("SELECT CompanyName FROM SalesLT.Customer", "user@example.com")

    rows = service.apply_masks([{"CustomerID": 1, "CompanyName": "Contoso"}], resources, decisions)

    assert rows[0]["CustomerID"] == 1
    assert rows[0]["CompanyName"] == "masked:Contoso"
