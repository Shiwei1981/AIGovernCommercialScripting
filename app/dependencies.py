from __future__ import annotations

from fastapi import Depends, Request

from app.data.repositories.customer_repository import CustomerRepository
from app.services.ad_copy_service import AdCopyService
from app.services.ai_logging_service import AILoggingService
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.entra_auth_service import EntraAuthService
from app.services.news_trend_service import NewsTrendService
from app.services.nl2sql_service import NL2SQLService
from app.services.product_bootstrap_service import ProductBootstrapService
from app.state import AppState


def get_state(request: Request) -> AppState:
    return request.app.state.container


def get_auth_service(state: AppState = Depends(get_state)) -> EntraAuthService:
    return EntraAuthService(state.settings, state.sessions)


def require_user(
    request: Request,
    auth_service: EntraAuthService = Depends(get_auth_service),
) -> dict:
    return auth_service.get_session_user(request)


def get_product_service(state: AppState = Depends(get_state)) -> ProductBootstrapService:
    return ProductBootstrapService(state.product_repository)


def get_ai_logging_service(state: AppState = Depends(get_state)) -> AILoggingService:
    return AILoggingService(state.settings, state.ai_log_repository)


def get_customer_repository(state: AppState = Depends(get_state)) -> CustomerRepository:
    return state.customer_repository


def get_nl2sql_service(
    state: AppState = Depends(get_state),
    ai_logging: AILoggingService = Depends(get_ai_logging_service),
) -> NL2SQLService:
    return NL2SQLService(state.settings, ai_logging)


def get_customer_analysis_service(
    state: AppState = Depends(get_state),
    ai_logging: AILoggingService = Depends(get_ai_logging_service),
) -> CustomerAnalysisService:
    return CustomerAnalysisService(state.settings, state.customer_repository, ai_logging)


def get_news_trend_service(
    state: AppState = Depends(get_state),
    ai_logging: AILoggingService = Depends(get_ai_logging_service),
) -> NewsTrendService:
    return NewsTrendService(state.settings, ai_logging)


def get_ad_copy_service(
    state: AppState = Depends(get_state),
    ai_logging: AILoggingService = Depends(get_ai_logging_service),
) -> AdCopyService:
    return AdCopyService(state.settings, ai_logging)
