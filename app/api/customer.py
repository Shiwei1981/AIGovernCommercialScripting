from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_customer_analysis_service,
    get_customer_repository,
    get_nl2sql_service,
    get_product_service,
    require_user,
)
from app.models.contracts import (
    CustomerAnalysisResponse,
    CustomerQueryRequest,
    CustomerQueryResponse,
)
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.nl2sql_service import NL2SQLService

router = APIRouter(prefix="/api/customers", tags=["customers"])
CUSTOMER_QUERY_MAX_RESULTS = 10


@router.post("/query", response_model=CustomerQueryResponse)
def query_customers(
    payload: CustomerQueryRequest,
    user: dict = Depends(require_user),
    nl2sql_service: NL2SQLService = Depends(get_nl2sql_service),
    customer_repo=Depends(get_customer_repository),
):
    sql = nl2sql_service.generate_sql(payload.customer_description, user_identity=user["user_id"])
    results = customer_repo.query_customers(sql, max_results=CUSTOMER_QUERY_MAX_RESULTS)
    return {"generated_sql": sql, "results": results}


@router.post("/{customer_id}/analysis", response_model=CustomerAnalysisResponse)
def customer_analysis(
    customer_id: int,
    user: dict = Depends(require_user),
    analysis_service: CustomerAnalysisService = Depends(get_customer_analysis_service),
    product_service=Depends(get_product_service),
):
    products = product_service.get_bootstrap_products()
    return analysis_service.analyze_customer(customer_id, user["user_id"], products)
