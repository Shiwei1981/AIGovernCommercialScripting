from __future__ import annotations

import re

from app.config import Settings
from app.data.repositories.customer_repository import CustomerRepository
from app.services.ai_client import invoke_model
from app.services.ai_logging_service import AILoggingService

_TOKEN_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]|[^\s\u3400-\u4dbf\u4e00-\u9fff]+")


class CustomerAnalysisService:
    def __init__(
        self,
        settings: Settings,
        customer_repository: CustomerRepository,
        ai_logging_service: AILoggingService,
    ) -> None:
        self._settings = settings
        self._customer_repository = customer_repository
        self._ai_logging_service = ai_logging_service

    def analyze_customer(self, customer_id: int, user_identity: str, products: list[dict]) -> dict:
        history = self._customer_repository.get_order_history(customer_id)
        profile = self._customer_repository.get_customer_profile(customer_id)
        prompt = (
            "Provide sales possibility analysis in <=500 words.\n"
            f"Customer profile: {profile}\n"
            f"Order history: {history}\n"
            f"Product context: {products[:5]}"
        )
        analysis = self._ai_logging_service.call_with_logging(
            step_name="customer_analysis",
            model_name=self._settings.openai_deployment,
            ai_input_raw=prompt,
            logged_in_user_identity=user_identity,
            callback=lambda: invoke_model(self._settings, prompt),
        )
        analysis = _truncate_analysis_text(analysis, max_tokens=500)
        return {"order_history": history, "analysis_text": analysis}


def _truncate_analysis_text(text: str, max_tokens: int) -> str:
    trimmed = text.strip()
    if not trimmed:
        return trimmed
    token_matches = list(_TOKEN_PATTERN.finditer(trimmed))
    if len(token_matches) <= max_tokens:
        return trimmed
    end_index = token_matches[max_tokens - 1].end()
    return trimmed[:end_index].rstrip()
