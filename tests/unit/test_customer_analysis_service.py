from __future__ import annotations

from types import SimpleNamespace

from app.services.customer_analysis_service import CustomerAnalysisService


class FakeCustomerRepository:
    def __init__(self) -> None:
        self.order_queries = 0

    def get_customer_order_line_items(self, customer_id, user_principal_name=None):  # noqa: ANN001
        self.order_queries += 1
        assert customer_id == 42
        assert user_principal_name == "user@example.com"
        return [{"product_name": "Road Tire", "order_qty": 1, "unit_price": 12.5, "unit_price_discount": 0}]

    def get_customer_profile(self, *_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Customer profile should come from the UI payload")


def test_prepare_analysis_prompt_uses_ui_context_without_profile_lookup():
    repo = FakeCustomerRepository()
    service = CustomerAnalysisService(
        SimpleNamespace(),
        repo,
        SimpleNamespace(),
    )

    result = service.prepare_analysis_prompt(
        42,
        "user@example.com",
        customer_profile={"customer_id": 42, "company_name": "Retail Co"},
        product_context={"product_id": 7, "product_name": "Road Tire"},
    )

    assert repo.order_queries == 1
    assert result["order_line_items"] == [
        {"product_name": "Road Tire", "order_qty": 1, "unit_price": 12.5, "unit_price_discount": 0}
    ]
    assert "Retail Co" in result["generated_prompt"]
    assert "Road Tire" in result["generated_prompt"]
