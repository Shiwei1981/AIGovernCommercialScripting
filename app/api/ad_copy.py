from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_ad_copy_service,
    get_customer_repository,
    get_product_service,
    require_user,
)
from app.errors import AppError
from app.models.contracts import AdCopyOutput, AdCopyRequest
from app.services.ad_copy_service import AdCopyService
from app.services.product_bootstrap_service import ProductBootstrapService

router = APIRouter(prefix="/api/ad-copy", tags=["ad-copy"])


@router.post("/generate", response_model=AdCopyOutput)
def generate_ad_copy(
    payload: AdCopyRequest,
    user: dict = Depends(require_user),
    ad_service: AdCopyService = Depends(get_ad_copy_service),
    product_service: ProductBootstrapService = Depends(get_product_service),
    customer_repo=Depends(get_customer_repository),
):
    products = product_service.get_bootstrap_products()
    product = next((p for p in products if int(p["product_id"]) == payload.product_id), None)
    if not product:
        raise AppError("Selected product not found.", 404)
    customer_profile = customer_repo.get_customer_profile(payload.customer_id)
    return ad_service.generate(
        customer_description=payload.customer_description,
        customer_profile=customer_profile,
        product=product,
        trend_summary=payload.trend_summary,
        user_identity=user["user_id"],
    )
