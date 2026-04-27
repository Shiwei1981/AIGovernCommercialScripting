from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_ad_copy_service,
    get_customer_repository,
    get_product_service,
    require_user,
)
from app.errors import AppError
from app.models.contracts import (
    AdCopyExecutionRequest,
    AdCopyOutput,
    AdCopyPreviewResponse,
    AdCopyRequest,
)
from app.services.ad_copy_service import AdCopyService
from app.services.product_bootstrap_service import ProductBootstrapService

router = APIRouter(prefix="/api/ad-copy", tags=["ad-copy"])


def _resolve_generation_inputs(
    payload: AdCopyRequest,
    user_identity: str,
    product_service: ProductBootstrapService,
    customer_repo,
) -> tuple[dict, dict]:
    product = payload.selected_product
    if not product:
        product = product_service.get_product_by_id(
            payload.product_id,
            user_principal_name=user_identity,
        )
        if not product:
            raise AppError("Selected product not found.", 404)
    customer_profile = payload.selected_customer
    if not customer_profile:
        customer_profile = customer_repo.get_customer_profile(
            payload.customer_id,
            user_principal_name=user_identity,
        )
    return product, customer_profile


@router.post("/preview", response_model=AdCopyPreviewResponse)
def preview_ad_copy_prompt(
    payload: AdCopyRequest,
    user: dict = Depends(require_user),
    ad_service: AdCopyService = Depends(get_ad_copy_service),
    product_service: ProductBootstrapService = Depends(get_product_service),
    customer_repo=Depends(get_customer_repository),
):
    user_identity = _user_upn(user)
    product, customer_profile = _resolve_generation_inputs(
        payload,
        user_identity,
        product_service,
        customer_repo,
    )
    return {
        "generated_prompt": ad_service.build_prompt(
            customer_description=payload.customer_description,
            customer_profile=customer_profile,
            product=product,
            trend_summary=payload.trend_summary,
        )
    }


@router.post("/execute", response_model=AdCopyOutput)
def execute_ad_copy_prompt(
    payload: AdCopyExecutionRequest,
    user: dict = Depends(require_user),
    ad_service: AdCopyService = Depends(get_ad_copy_service),
):
    return ad_service.execute_prompt(payload.generated_prompt, _user_upn(user))


@router.post("/generate", response_model=AdCopyOutput)
def generate_ad_copy(
    payload: AdCopyRequest,
    user: dict = Depends(require_user),
    ad_service: AdCopyService = Depends(get_ad_copy_service),
    product_service: ProductBootstrapService = Depends(get_product_service),
    customer_repo=Depends(get_customer_repository),
):
    user_identity = _user_upn(user)
    product, customer_profile = _resolve_generation_inputs(
        payload,
        user_identity,
        product_service,
        customer_repo,
    )
    return ad_service.generate(
        customer_description=payload.customer_description,
        customer_profile=customer_profile,
        product=product,
        trend_summary=payload.trend_summary,
        user_identity=user_identity,
    )


def _user_upn(user: dict) -> str:
    return user.get("user_principal_name") or user.get("email") or user["user_id"]
