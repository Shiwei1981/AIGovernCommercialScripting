from __future__ import annotations

from typing import Any

from app.config import Settings
from app.data.repositories.customer_repository import CustomerRepository
from app.services.ai_client import invoke_model
from app.services.ai_logging_service import AILoggingService
from app.services.text_truncation import truncate_text_by_token_count


class CustomerAnalysisService:
    def __init__(
        self,
        settings: Settings,
        customer_repository: CustomerRepository,
        ai_logging_service: AILoggingService,
    ) -> None:
        self._settings = settings
        self._customer_repository = customer_repository
        self._ai_logging_service = ai_logging_service

    def prepare_analysis_prompt(
        self,
        customer_id: int,
        user_identity: str,
        customer_profile: dict[str, Any] | None = None,
        product_context: dict[str, Any] | None = None,
    ) -> dict:
        order_line_items = self._customer_repository.get_customer_order_line_items(
            customer_id,
            user_principal_name=user_identity,
        )
        profile = _customer_context(customer_id, customer_profile)
        prompt = (
            "Provide sales possibility analysis in <=200 words.\n"
            f"Customer profile: {profile}\n"
            f"Order line items: {order_line_items}\n"
            f"Product context: {product_context or {}}"
        )
        return {"order_line_items": order_line_items, "generated_prompt": prompt}

    def analyze_customer(
        self,
        customer_id: int,
        user_identity: str,
        customer_profile: dict[str, Any] | None = None,
        product_context: dict[str, Any] | None = None,
    ) -> dict:
        preview = self.prepare_analysis_prompt(
            customer_id,
            user_identity,
            customer_profile,
            product_context,
        )
        analysis = self.execute_analysis_prompt(preview["generated_prompt"], user_identity)
        return {
            "order_history": _summarize_order_line_items(customer_id, preview["order_line_items"]),
            "order_line_items": preview["order_line_items"],
            "generated_prompt": preview["generated_prompt"],
            "analysis_text": analysis,
        }

    def execute_analysis_prompt(self, prompt: str, user_identity: str) -> str:
        analysis = self._ai_logging_service.call_with_logging(
            step_name="customer_analysis",
            model_name=self._settings.openai_deployment,
            ai_input_raw=prompt,
            logged_in_user_identity=user_identity,
            callback=lambda: invoke_model(self._settings, prompt),
        )
        return _truncate_analysis_text(analysis, max_tokens=200)


def _customer_context(customer_id: int, customer_profile: dict[str, Any] | None) -> dict[str, Any]:
    profile = dict(customer_profile or {})
    profile["customer_id"] = customer_id
    return profile


def _summarize_order_line_items(customer_id: int, line_items: list[dict[str, Any]]) -> dict:
    total_amount = 0.0
    last_order_date = None
    for item in line_items:
        total_amount += _estimated_line_amount(item)
        order_date = item.get("order_date")
        if order_date is not None and (last_order_date is None or str(order_date) > last_order_date):
            last_order_date = str(order_date)
    return {
        "customer_id": customer_id,
        "total_orders": len(line_items),
        "total_amount": total_amount,
        "last_order_date": last_order_date,
        "orders": line_items,
    }


def _estimated_line_amount(item: dict[str, Any]) -> float:
    order_qty = _to_float(item.get("order_qty"))
    unit_price = _to_float(item.get("unit_price"))
    discount = _to_float(item.get("unit_price_discount"))
    return order_qty * unit_price * max(0.0, 1.0 - discount)


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _truncate_analysis_text(text: str, max_tokens: int) -> str:
    return truncate_text_by_token_count(text, max_tokens)
