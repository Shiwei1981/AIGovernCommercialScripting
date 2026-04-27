from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_news_trend_service, get_product_service, require_user
from app.errors import AppError
from app.models.contracts import (
    TrendSearchPreviewResponse,
    TrendSearchRequest,
    TrendSearchResponse,
    TrendSummaryExecutionRequest,
)
from app.services.news_trend_service import NewsTrendService
from app.services.product_bootstrap_service import ProductBootstrapService

router = APIRouter(prefix="/api/trends", tags=["trends"])


def _resolve_product(
    payload: TrendSearchRequest,
    user_identity: str,
    product_service: ProductBootstrapService,
) -> dict:
    if payload.selected_product:
        return payload.selected_product
    product = product_service.get_product_by_id(
        payload.product_id,
        user_principal_name=user_identity,
    )
    if not product:
        raise AppError("Selected product not found.", 404)
    return product


@router.post("/search", response_model=TrendSearchResponse)
def search_trend(
    payload: TrendSearchRequest,
    user: dict = Depends(require_user),
    trend_service: NewsTrendService = Depends(get_news_trend_service),
    product_service: ProductBootstrapService = Depends(get_product_service),
):
    user_identity = _user_upn(user)
    product = _resolve_product(payload, user_identity, product_service)
    return trend_service.search_trends(product, user_identity)


@router.post("/search/preview", response_model=TrendSearchPreviewResponse)
def preview_trend_prompt(
    payload: TrendSearchRequest,
    user: dict = Depends(require_user),
    trend_service: NewsTrendService = Depends(get_news_trend_service),
    product_service: ProductBootstrapService = Depends(get_product_service),
):
    user_identity = _user_upn(user)
    product = _resolve_product(payload, user_identity, product_service)
    return trend_service.prepare_trend_summary_prompt(product, user_identity)


@router.post("/search/execute", response_model=TrendSearchResponse)
def execute_trend_prompt(
    payload: TrendSummaryExecutionRequest,
    user: dict = Depends(require_user),
    trend_service: NewsTrendService = Depends(get_news_trend_service),
):
    user_identity = _user_upn(user)
    return trend_service.execute_trend_summary(
        search_query=payload.search_query,
        news_items=[item.model_dump() for item in payload.news_items],
        prompt=payload.generated_prompt,
        valid_ratio=payload.valid_ratio,
        fetch_errors=payload.fetch_errors,
        user_identity=user_identity,
    )


def _user_upn(user: dict) -> str:
    return user.get("user_principal_name") or user.get("email") or user["user_id"]
