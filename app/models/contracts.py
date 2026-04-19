from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    user_id: str
    tenant_id: str
    display_name: str | None = None
    email: str | None = None


class SessionState(BaseModel):
    authenticated: bool
    user: UserInfo | None = None


class ProductDisplayItem(BaseModel):
    product_id: int
    product_name: str
    category_name: str
    model_name: str | None = None
    description: str | None = None


class CustomerQueryRequest(BaseModel):
    customer_description: str = Field(min_length=1)


class CustomerMatchResult(BaseModel):
    customer_id: int
    customer_name: str
    company_name: str | None = None
    location: str | None = None
    relevance_score: float
    match_reason: str | None = None
    order_count: int = 0
    lifetime_value: float = 0.0


class CustomerQueryResponse(BaseModel):
    generated_sql: str
    results: list[CustomerMatchResult]


class CustomerOrderHistory(BaseModel):
    customer_id: int
    total_orders: int
    total_amount: float
    last_order_date: str | None = None
    orders: list[dict[str, Any]]


class CustomerAnalysisResponse(BaseModel):
    order_history: CustomerOrderHistory
    analysis_text: str


class TrendSearchRequest(BaseModel):
    product_id: int


class TrendNewsEvidenceItem(BaseModel):
    title: str
    rss_link: str
    publisher_url: str | None = None
    source_name: str | None = None
    published_at: str | None = None
    summary_snippet: str | None = None
    fetch_status: str
    is_valid_evidence: bool
    error_message: str | None = None


class TrendSummary(BaseModel):
    summary_text: str
    citations: list[dict[str, str]]
    valid_ratio: float
    fetch_errors: list[str]


class TrendSearchResponse(BaseModel):
    search_query: str
    news_items: list[TrendNewsEvidenceItem]
    summary: TrendSummary


class AdCopyRequest(BaseModel):
    customer_description: str = Field(min_length=1)
    customer_id: int
    product_id: int
    trend_summary: str = Field(min_length=1)


class AdCopyOutput(BaseModel):
    ad_copy_text: str
    generated_at: datetime


class ResetResponse(BaseModel):
    status: str
    message: str
