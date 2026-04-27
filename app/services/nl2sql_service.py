from __future__ import annotations

import re

import sqlglot
from sqlglot import expressions as exp

from app.config import Settings
from app.errors import AppError
from app.services.ai_client import invoke_model
from app.services.ai_logging_service import AILoggingService

DENYLIST = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bMERGE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
    r"\bEXEC\b",
    r";.+\S",
]

ALLOWED_TABLES = ["Customer", "CustomerAddress", "Address", "SalesOrderHeader", "SalesOrderDetail"]
ALLOWED_TABLE_BY_LOWER = {table.lower(): table for table in ALLOWED_TABLES}
SALES_SCHEMA = "SalesLT"


def validate_select_only(sql: str) -> None:
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        raise AppError("Only SELECT statements are allowed.", 400)
    for pattern in DENYLIST:
        if re.search(pattern, normalized):
            raise AppError("Generated SQL violates read-only policy.", 400)


def qualify_saleslt_schema(sql: str) -> str:
    try:
        expression = sqlglot.parse_one(sql.strip().rstrip(";"), read="tsql")
    except sqlglot.errors.ParseError as exc:
        raise AppError("Generated SQL could not be parsed.", 400) from exc
    if expression is None:
        raise AppError("Generated SQL could not be parsed.", 400)
    cte_names = {
        _normalize_identifier(str(cte.alias)).lower()
        for cte in expression.find_all(exp.CTE)
        if cte.alias
    }
    for table in expression.find_all(exp.Table):
        table_name = _normalize_identifier(str(table.name))
        if not str(table.db or "") and table_name.lower() in cte_names:
            continue
        actual_table = _allowed_table_name(table_name)
        if actual_table is None:
            continue
        table.set("this", exp.to_identifier(actual_table))
        table.set("db", exp.to_identifier(SALES_SCHEMA))
        table.set("catalog", None)
    return expression.sql(dialect="tsql")


def _allowed_table_name(identifier: str) -> str | None:
    parts = [_normalize_identifier(part) for part in identifier.split(".") if part]
    table_name = parts[-1] if parts else identifier
    return ALLOWED_TABLE_BY_LOWER.get(table_name.lower())


def _normalize_identifier(value: str) -> str:
    normalized = value.strip()
    while len(normalized) >= 2 and (
        (normalized[0] == "[" and normalized[-1] == "]")
        or (normalized[0] == '"' and normalized[-1] == '"')
    ):
        normalized = normalized[1:-1].strip()
    return normalized


class NL2SQLService:
    def __init__(self, settings: Settings, ai_logging_service: AILoggingService):
        self._settings = settings
        self._ai_logging_service = ai_logging_service

    def generate_sql(self, customer_description: str, user_identity: str) -> str:
        prompt = (
            "Generate one SQL SELECT statement (no markdown) to rank customers by relevance.\n"
            "Use schema-qualified table names with SalesLT.\n"
            "Do not use SELECT * or SQL views; select explicit base-table columns only.\n"
            "Join SalesLT.Customer, SalesLT.CustomerAddress, and SalesLT.Address to return address data.\n"
            "Return columns with exact aliases: customer_id, customer_name, company_name, relevance_score, "
            "address_line1, address_line2, city, state_province, country_region, postal_code.\n"
            "Do not return location, match_reason, order_count, lifetime_value, or other extra columns.\n"
            "Order results by relevance_score DESC.\n"
            "Allowed tables: SalesLT.Customer, SalesLT.CustomerAddress, SalesLT.Address, "
            "SalesLT.SalesOrderHeader, SalesLT.SalesOrderDetail.\n"
            f"Customer targeting request: {customer_description}\n"
        )
        sql = self._ai_logging_service.call_with_logging(
            step_name="nl_to_sql",
            model_name=self._settings.openai_deployment,
            ai_input_raw=prompt,
            logged_in_user_identity=user_identity,
            callback=lambda: invoke_model(self._settings, prompt),
        )
        validate_select_only(sql)
        return qualify_saleslt_schema(sql)
