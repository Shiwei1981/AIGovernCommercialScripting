from __future__ import annotations

import re
from typing import Any

from app.config import Settings
from app.data.repositories.mock_data import CUSTOMERS, ORDERS
from app.data.sql_client import SqlClient
from app.errors import AppError

DEFAULT_CUSTOMER_QUERY_LIMIT = 4
HARD_MAX_CUSTOMER_QUERY_LIMIT = 4
CUSTOMER_ORDER_LINE_ITEM_LIMIT = 4


class CustomerRepository:
    def __init__(self, sql_client: SqlClient | None, settings: Settings) -> None:
        self._sql_client = sql_client
        self._settings = settings

    def query_customers(
        self,
        generated_sql: str,
        max_results: int = DEFAULT_CUSTOMER_QUERY_LIMIT,
        user_principal_name: str | None = None,
    ) -> list[dict]:
        limit = _normalize_limit(max_results)
        if self._sql_client is None:
            return sorted(CUSTOMERS, key=lambda row: row["relevance_score"], reverse=True)[:limit]
        sql_body = generated_sql.strip().rstrip(";")
        sql = _inject_top_limit(sql_body, min(self._settings.sql_max_rows, limit))
        rows = self._sql_client.query(sql, user_principal_name=user_principal_name)
        normalized = _normalize_customer_rows(rows)[:limit]
        self._attach_company_names(normalized, user_principal_name=user_principal_name)
        return normalized

    def get_order_history(self, customer_id: int, user_principal_name: str | None = None) -> dict:
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
            user_principal_name=user_principal_name,
        )
        if not rows:
            customer_rows = self._sql_client.query(
                "SELECT TOP 1 CustomerID AS customer_id FROM SalesLT.Customer WHERE CustomerID = ?",
                (customer_id,),
                user_principal_name=user_principal_name,
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

    def get_customer_order_line_items(
        self,
        customer_id: int,
        user_principal_name: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._sql_client is None:
            rows: list[dict[str, Any]] = []
            for order in ORDERS.get(customer_id, []):
                rows.append(
                    {
                        "order_qty": 1,
                        "unit_price": float(order["total_due"]),
                        "unit_price_discount": 0.0,
                        "order_date": order["order_date"],
                        "sub_total": float(order["total_due"]),
                        "product_name": "Demo Product",
                    }
                )
            if rows:
                return rows[:CUSTOMER_ORDER_LINE_ITEM_LIMIT]
            customer_exists = any(item.get("customer_id") == customer_id for item in CUSTOMERS)
            if not customer_exists:
                raise AppError("Customer not found", status_code=404)
            return []
        return self._sql_client.query(
            f"""
            SELECT TOP {CUSTOMER_ORDER_LINE_ITEM_LIMIT}
                sod.OrderQty AS order_qty,
                sod.UnitPrice AS unit_price,
                sod.UnitPriceDiscount AS unit_price_discount,
                soh.OrderDate AS order_date,
                soh.SubTotal AS sub_total,
                p.Name AS product_name
            FROM SalesLT.SalesOrderHeader soh
            JOIN SalesLT.SalesOrderDetail sod ON soh.SalesOrderID = sod.SalesOrderID
            JOIN SalesLT.Product p ON sod.ProductID = p.ProductID
            WHERE soh.CustomerID = ?
            ORDER BY soh.OrderDate DESC, p.Name
            """,
            (customer_id,),
            user_principal_name=user_principal_name,
        )

    def get_customer_profile(self, customer_id: int, user_principal_name: str | None = None) -> dict:
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
            user_principal_name=user_principal_name,
        )
        if not rows:
            raise AppError("Customer not found", status_code=404)
        return rows[0]

    def _attach_company_names(
        self,
        customers: list[dict[str, Any]],
        user_principal_name: str | None = None,
    ) -> None:
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
            user_principal_name=user_principal_name,
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
        return re.sub(
            r"(?is)^(\s*select\s+(?:distinct\s+)?top\s*)(?:\(\s*)?\d+(?:\s*\))?",
            rf"\g<1>{limit}",
            sql_body,
            count=1,
        )
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
    normalized_by_id: dict[int, dict[str, Any]] = {}
    order: list[int] = []
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
        address = _address_from_row(row_by_key)
        if customer_id not in normalized_by_id:
            normalized_by_id[customer_id] = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "company_name": company_name,
                "location": location,
                "addresses": [],
                "address_display": None,
                "relevance_score": relevance_score,
                "match_reason": match_reason,
                "order_count": order_count if order_count is not None else 0,
                "lifetime_value": lifetime_value,
            }
            order.append(customer_id)
        existing = normalized_by_id[customer_id]
        if address and address not in existing["addresses"]:
            existing["addresses"].append(address)
        existing["address_display"] = _join_address_display(existing["addresses"]) or existing.get("location")
    normalized = [normalized_by_id[customer_id] for customer_id in order]
    if rows and not normalized:
        raise AppError(
            "Customer query returned incompatible columns. Please retry with a clearer description.",
            status_code=400,
        )
    return normalized


def _address_from_row(row_by_key: dict[str, Any]) -> dict[str, str | None] | None:
    address = {
        "address_line1": _string_or_none(_pick_first(row_by_key, "address_line1", "addressline1")),
        "address_line2": _string_or_none(_pick_first(row_by_key, "address_line2", "addressline2")),
        "city": _string_or_none(_pick_first(row_by_key, "city")),
        "state_province": _string_or_none(
            _pick_first(row_by_key, "state_province", "stateprovince", "state")
        ),
        "country_region": _string_or_none(
            _pick_first(row_by_key, "country_region", "countryregion", "country")
        ),
        "postal_code": _string_or_none(_pick_first(row_by_key, "postal_code", "postalcode", "zip")),
    }
    formatted = _format_address(address)
    if not formatted:
        return None
    return {**address, "formatted_address": formatted}


def _format_address(address: dict[str, str | None]) -> str:
    street = " ".join(
        part
        for part in [address.get("address_line1"), address.get("address_line2")]
        if part
    )
    city_state_postal = " ".join(
        part
        for part in [
            ", ".join(part for part in [address.get("city"), address.get("state_province")] if part),
            address.get("postal_code"),
        ]
        if part
    )
    parts = [part for part in [street, city_state_postal, address.get("country_region")] if part]
    return ", ".join(parts)


def _join_address_display(addresses: list[dict[str, str | None]]) -> str | None:
    formatted = [str(item["formatted_address"]) for item in addresses if item.get("formatted_address")]
    return "; ".join(formatted) if formatted else None


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
