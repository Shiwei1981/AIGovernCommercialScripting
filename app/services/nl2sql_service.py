from __future__ import annotations

import re

from app.config import Settings
from app.errors import AppError
from app.services.ai_client import invoke_model
from app.services.ai_logging_service import AILoggingService

DENYLIST = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bEXEC\b",
    r";.+\S",
]

ALLOWED_TABLES = ["Customer", "CustomerAddress", "Address", "SalesOrderHeader", "SalesOrderDetail"]


def validate_select_only(sql: str) -> None:
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        raise AppError("Only SELECT statements are allowed.", 400)
    for pattern in DENYLIST:
        if re.search(pattern, normalized):
            raise AppError("Generated SQL violates read-only policy.", 400)


def qualify_saleslt_schema(sql: str) -> str:
    qualified = sql
    for table in ALLOWED_TABLES:
        qualified = re.sub(
            rf"(?i)(?<![\w.\]])\b{table}\b",
            f"SalesLT.{table}",
            qualified,
        )
    return qualified


class NL2SQLService:
    def __init__(self, settings: Settings, ai_logging_service: AILoggingService):
        self._settings = settings
        self._ai_logging_service = ai_logging_service

    def generate_sql(self, customer_description: str, user_identity: str) -> str:
        prompt = (
            "Generate one SQL SELECT statement (no markdown) to rank customers by relevance.\n"
            "Use schema-qualified table names with SalesLT.\n"
            "Return columns with exact aliases: customer_id, customer_name, relevance_score.\n"
            "Optional aliases: company_name, location, match_reason, order_count, lifetime_value.\n"
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
