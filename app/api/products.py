from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_product_service, require_user
from app.models.contracts import ProductDisplayItem
from app.services.product_bootstrap_service import ProductBootstrapService

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/bootstrap", response_model=list[ProductDisplayItem])
def bootstrap_products(
    _: dict = Depends(require_user),
    service: ProductBootstrapService = Depends(get_product_service),
):
    return service.get_bootstrap_products()
