from __future__ import annotations

import re
from typing import Any

from app.config import Settings
from app.data.repositories.mock_data import CUSTOMERS, ORDERS
from app.data.sql_client import SqlClient
from app.errors import AppError

DEFAULT_CUSTOMER_QUERY_LIMIT = 10
HARD_MAX_CUSTOMER_QUERY_LIMIT = 10


class CustomerRepository:
    def __init__(self, sql_client: SqlClient | None, settings: Settings) -> None:
        self._sql_client = sql_client
        self._settings = settings

    def query_customers(self, generated_sql: str, max_results: int = DEFAULT_CUSTOMER_QUERY_LIMIT) -> list[dict]:
        limit = _normalize_limit(max_results)
        if self._sql_client is None:
            return sorted(CUSTOMERS, key=lambda row: row["relevance_score"], reverse=True)[:limit]
        sql_body = generated_sql.strip().rstrip(";")
        sql = _inject_top_limit(sql_body, min(self._settings.sql_max_rows, limit))
        rows = self._sql_client.query(sql)
        normalized = _normalize_customer_rows(rows)[:limit]
        self._attach_company_names(normalized)
        return normalized

    def get_order_history(self, customer_id: int) -> dict:
        if self._sql_client is None:
            orders = ORDERS.get(customer_id, [])
            if not orders:
                customer_exists = any(item.get("customer_id") == customer_id for item in CUSTOMERS)
                if not customer_exists:
                    raise AppError("Customer not found", status_code=404)
                return {
                    "customer_id": customer_id,
                    "total_orders": 0,
                    "total_amount": 0.0,
                    "last_order_date": None,
                    "orders": [],
                }
            total = sum(item["total_due"] for item in orders)
            return {
                "customer_id": customer_id,
                "total_orders": len(orders),
                "total_amount": total,
                "last_order_date": max(item["order_date"] for item in orders),
                "orders": orders,
            }
        rows = self._sql_client.query(
            "SELECT SalesOrderID AS order_id, OrderDate AS order_date, TotalDue AS total_due "
            "FROM SalesLT.SalesOrderHeader WHERE CustomerID = ? ORDER BY OrderDate DESC",
            (customer_id,),
        )
        if not rows:
            customer_rows = self._sql_client.query(
                "SELECT TOP 1 CustomerID AS customer_id FROM SalesLT.Customer WHERE CustomerID = ?",
                (customer_id,),
            )
            if not customer_rows:
                raise AppError("Customer not found", status_code=404)
            return {
                "customer_id": customer_id,
                "total_orders": 0,
                "total_amount": 0.0,
                "last_order_date": None,
                "orders": [],
            }
        total = float(sum(float(item["total_due"]) for item in rows))
        return {
            "customer_id": customer_id,
            "total_orders": len(rows),
            "total_amount": total,
            "last_order_date": str(rows[0]["order_date"]),
            "orders": rows,
        }

    def get_customer_profile(self, customer_id: int) -> dict:
        if self._sql_client is None:
            for c in CUSTOMERS:
                if c["customer_id"] == customer_id:
                    return c
            raise AppError("Customer not found", status_code=404)
        rows = self._sql_client.query(
            "SELECT TOP 1 CustomerID AS customer_id, "
            "COALESCE(FirstName + ' ' + LastName, CompanyName) AS customer_name "
            "FROM SalesLT.Customer WHERE CustomerID = ?",
            (customer_id,),
        )
        if not rows:
            raise AppError("Customer not found", status_code=404)
        return rows[0]

    def _attach_company_names(self, customers: list[dict[str, Any]]) -> None:
        if self._sql_client is None or not customers:
            return
        missing_ids = sorted(
            {
                customer["customer_id"]
                for customer in customers
                if customer.get("customer_id") is not None and not customer.get("company_name")
            }
        )
        if not missing_ids:
            return
        placeholders = ", ".join("?" for _ in missing_ids)
        rows = self._sql_client.query(
            "SELECT CustomerID AS customer_id, CompanyName AS company_name "
            f"FROM SalesLT.Customer WHERE CustomerID IN ({placeholders})",
            tuple(missing_ids),
        )
        company_by_id: dict[int, str] = {}
        for row in rows:
            row_by_key = {_canonical_key(key): value for key, value in row.items()}
            customer_id = _to_int(_pick_first(row_by_key, "customer_id", "customerid"))
            company_name = _string_or_none(_pick_first(row_by_key, "company_name", "companyname"))
            if customer_id is not None and company_name is not None:
                company_by_id[customer_id] = company_name
        for customer in customers:
            customer_id = _to_int(customer.get("customer_id"))
            if customer_id is None or customer.get("company_name"):
                continue
            customer["company_name"] = company_by_id.get(customer_id)


def _inject_top_limit(sql_body: str, limit: int) -> str:
    if re.match(r"(?is)^\s*select\s+(?:distinct\s+)?top\b", sql_body):
        return sql_body
    if re.match(r"(?is)^\s*select\s+distinct\s+", sql_body):
        return re.sub(
            r"(?is)^(\s*select\s+distinct\s+)",
            rf"\1TOP {limit} ",
            sql_body,
            count=1,
        )
    return re.sub(r"(?is)^(\s*select\s+)", rf"\1TOP {limit} ", sql_body, count=1)


def _normalize_limit(limit: int) -> int:
    try:
        parsed = int(limit)
    except (TypeError, ValueError):
        parsed = DEFAULT_CUSTOMER_QUERY_LIMIT
    return max(1, min(parsed, HARD_MAX_CUSTOMER_QUERY_LIMIT))


def _normalize_customer_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    total_rows = max(len(rows), 1)
    for idx, row in enumerate(rows):
        row_by_key = {_canonical_key(key): value for key, value in row.items()}
        customer_id = _to_int(_pick_first(row_by_key, "customer_id", "customerid", "id"))
        if customer_id is None:
            continue
        company_name = _string_or_none(_pick_first(row_by_key, "company_name", "companyname"))
        customer_name = _string_or_none(
            _pick_first(row_by_key, "customer_name", "customername", "name")
        )
        if customer_name is None:
            if company_name is not None:
                customer_name = company_name
            else:
                first_name = _string_or_none(_pick_first(row_by_key, "first_name", "firstname"))
                last_name = _string_or_none(_pick_first(row_by_key, "last_name", "lastname"))
                customer_name = (
                    " ".join(part for part in [first_name, last_name] if part) or f"Customer {customer_id}"
                )
        if company_name is None and customer_name and " " not in customer_name:
            company_name = customer_name
        relevance_score = _to_float(
            _pick_first(
                row_by_key,
                "relevance_score",
                "relevancescore",
                "score",
                "total_order_amount",
                "totalorderamount",
                "lifetime_value",
                "lifetimevalue",
                "total_due",
                "totaldue",
            ),
            fallback=round(1.0 - (idx / total_rows), 4),
        )
        location = _string_or_none(_pick_first(row_by_key, "location", "city_state", "stateprovince"))
        if location is None:
            city = _string_or_none(_pick_first(row_by_key, "city"))
            state = _string_or_none(_pick_first(row_by_key, "state", "state_province"))
            if city and state:
                location = f"{city}, {state}"
            else:
                location = city or state
        match_reason = _string_or_none(_pick_first(row_by_key, "match_reason", "matchreason", "reason"))
        order_count = _to_int(_pick_first(row_by_key, "order_count", "ordercount", "total_orders"), default=0)
        lifetime_value = _to_float(
            _pick_first(
                row_by_key,
                "lifetime_value",
                "lifetimevalue",
                "total_order_amount",
                "totalorderamount",
                "total_due",
                "totaldue",
            ),
            fallback=0.0,
        )
        normalized.append(
            {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "company_name": company_name,
                "location": location,
                "relevance_score": relevance_score,
                "match_reason": match_reason,
                "order_count": order_count if order_count is not None else 0,
                "lifetime_value": lifetime_value,
            }
        )
    if rows and not normalized:
        raise AppError(
            "Customer query returned incompatible columns. Please retry with a clearer description.",
            status_code=400,
        )
    return normalized


def _canonical_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _pick_first(row_by_key: dict[str, Any], *candidates: str) -> Any | None:
    for candidate in candidates:
        value = row_by_key.get(_canonical_key(candidate))
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _to_int(value: Any | None, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def _to_float(value: Any | None, fallback: float) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _string_or_none(value: Any | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
