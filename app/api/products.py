from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_product_service, require_user
from app.models.contracts import ProductDisplayItem, ProductPageResponse
from app.services.product_bootstrap_service import ProductBootstrapService

router = APIRouter(prefix="/api/products", tags=["products"])
DEFAULT_PRODUCT_PAGE_SIZE = 4
MAX_PRODUCT_PAGE_SIZE = 20


@router.get("", response_model=ProductPageResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PRODUCT_PAGE_SIZE, ge=1, le=MAX_PRODUCT_PAGE_SIZE),
    user: dict = Depends(require_user),
    service: ProductBootstrapService = Depends(get_product_service),
):
    return service.get_products_page(
        page=page,
        page_size=page_size,
        user_principal_name=_user_upn(user),
    )


@router.get("/bootstrap", response_model=list[ProductDisplayItem])
def bootstrap_products(
    user: dict = Depends(require_user),
    service: ProductBootstrapService = Depends(get_product_service),
):
    return service.get_bootstrap_products(user_principal_name=_user_upn(user))


def _user_upn(user: dict) -> str:
    return user.get("user_principal_name") or user.get("email") or user["user_id"]
