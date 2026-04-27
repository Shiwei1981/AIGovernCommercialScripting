from __future__ import annotations

from app.api.ad_copy import preview_ad_copy_prompt
from app.api.trend import preview_trend_prompt
from app.models.contracts import AdCopyRequest, TrendSearchRequest


class RaisingProductService:
    def get_product_by_id(self, *_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Product context should come from the UI payload")


class RaisingCustomerRepository:
    def get_customer_profile(self, *_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Customer context should come from the UI payload")


class FakeTrendService:
    def prepare_trend_summary_prompt(self, product, user_identity):  # noqa: ANN001
        return {
            "search_query": "road tire demand",
            "news_items": [],
            "generated_prompt": f"{user_identity}:{product['product_name']}",
            "valid_ratio": 0,
            "fetch_errors": [],
        }


class FakeAdCopyService:
    def build_prompt(self, *, customer_description, customer_profile, product, trend_summary):  # noqa: ANN001
        return (
            f"{customer_description}|{customer_profile['company_name']}|"
            f"{product['product_name']}|{trend_summary}"
        )


def test_trend_preview_uses_ui_product_context_without_product_lookup():
    result = preview_trend_prompt(
        TrendSearchRequest(
            product_id=7,
            selected_product={"product_id": 7, "product_name": "Road Tire"},
        ),
        user={"user_principal_name": "user@example.com", "user_id": "user"},
        trend_service=FakeTrendService(),
        product_service=RaisingProductService(),
    )

    assert result["generated_prompt"] == "user@example.com:Road Tire"


def test_ad_copy_preview_uses_ui_context_without_customer_or_product_lookup():
    result = preview_ad_copy_prompt(
        AdCopyRequest(
            customer_description="bike store",
            customer_id=42,
            product_id=7,
            trend_summary="strong demand",
            selected_customer={"customer_id": 42, "company_name": "Retail Co"},
            selected_product={"product_id": 7, "product_name": "Road Tire"},
        ),
        user={"user_principal_name": "user@example.com", "user_id": "user"},
        ad_service=FakeAdCopyService(),
        product_service=RaisingProductService(),
        customer_repo=RaisingCustomerRepository(),
    )

    assert result == {"generated_prompt": "bike store|Retail Co|Road Tire|strong demand"}
