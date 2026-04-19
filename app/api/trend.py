from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_news_trend_service, get_product_service, require_user
from app.errors import AppError
from app.models.contracts import TrendSearchRequest, TrendSearchResponse
from app.services.news_trend_service import NewsTrendService
from app.services.product_bootstrap_service import ProductBootstrapService

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.post("/search", response_model=TrendSearchResponse)
def search_trend(
    payload: TrendSearchRequest,
    user: dict = Depends(require_user),
    trend_service: NewsTrendService = Depends(get_news_trend_service),
    product_service: ProductBootstrapService = Depends(get_product_service),
):
    products = product_service.get_bootstrap_products()
    product = next((p for p in products if int(p["product_id"]) == payload.product_id), None)
    if not product:
        raise AppError("Selected product not found.", 404)
    return trend_service.search_trends(product, user["user_id"])
