from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_customer_analysis_service,
    get_customer_repository,
    get_nl2sql_service,
    require_user,
)
from app.models.contracts import (
    CustomerAnalysisExecutionRequest,
    CustomerAnalysisPreviewRequest,
    CustomerAnalysisPreviewResponse,
    CustomerAnalysisResponse,
    CustomerQueryRequest,
    CustomerQueryResponse,
)
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.nl2sql_service import NL2SQLService

router = APIRouter(prefix="/api/customers", tags=["customers"])
CUSTOMER_QUERY_MAX_RESULTS = 4


@router.post("/query", response_model=CustomerQueryResponse)
def query_customers(
    payload: CustomerQueryRequest,
    user: dict = Depends(require_user),
    nl2sql_service: NL2SQLService = Depends(get_nl2sql_service),
    customer_repo=Depends(get_customer_repository),
):
    user_identity = _user_upn(user)
    sql = nl2sql_service.generate_sql(payload.customer_description, user_identity=user_identity)
    results = customer_repo.query_customers(
        sql,
        max_results=CUSTOMER_QUERY_MAX_RESULTS,
        user_principal_name=user_identity,
    )
    return {"generated_sql": sql, "results": results}


@router.post("/{customer_id}/analysis/preview", response_model=CustomerAnalysisPreviewResponse)
def customer_analysis_preview(
    customer_id: int,
    payload: CustomerAnalysisPreviewRequest | None = None,
    user: dict = Depends(require_user),
    analysis_service: CustomerAnalysisService = Depends(get_customer_analysis_service),
):
    user_identity = _user_upn(user)
    return analysis_service.prepare_analysis_prompt(
        customer_id,
        user_identity,
        customer_profile=(payload.selected_customer if payload else None),
        product_context=(payload.selected_product if payload else None),
    )


@router.post("/{customer_id}/analysis/execute", response_model=CustomerAnalysisResponse)
def customer_analysis_execute(
    customer_id: int,
    payload: CustomerAnalysisExecutionRequest,
    user: dict = Depends(require_user),
    analysis_service: CustomerAnalysisService = Depends(get_customer_analysis_service),
):
    user_identity = _user_upn(user)
    analysis_text = analysis_service.execute_analysis_prompt(payload.generated_prompt, user_identity)
    return {
        "order_history": {
            "customer_id": customer_id,
            "total_orders": 0,
            "total_amount": 0.0,
            "last_order_date": None,
            "orders": [],
        },
        "order_line_items": [],
        "generated_prompt": payload.generated_prompt,
        "analysis_text": analysis_text,
    }


@router.post("/{customer_id}/analysis", response_model=CustomerAnalysisResponse)
def customer_analysis(
    customer_id: int,
    payload: CustomerAnalysisPreviewRequest | None = None,
    user: dict = Depends(require_user),
    analysis_service: CustomerAnalysisService = Depends(get_customer_analysis_service),
):
    user_identity = _user_upn(user)
    return analysis_service.analyze_customer(
        customer_id,
        user_identity,
        customer_profile=(payload.selected_customer if payload else None),
        product_context=(payload.selected_product if payload else None),
    )


def _user_upn(user: dict) -> str:
    return user.get("user_principal_name") or user.get("email") or user["user_id"]
