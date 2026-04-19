from __future__ import annotations

from datetime import UTC, datetime

from app.config import Settings
from app.services.ai_client import invoke_model
from app.services.ai_logging_service import AILoggingService


class AdCopyService:
    def __init__(self, settings: Settings, ai_logging_service: AILoggingService):
        self._settings = settings
        self._ai_logging_service = ai_logging_service

    def generate(
        self,
        *,
        customer_description: str,
        customer_profile: dict,
        product: dict,
        trend_summary: str,
        user_identity: str,
    ) -> dict:
        prompt = (
            "Create ad copy in <=500 words.\n"
            f"Customer intent: {customer_description}\n"
            f"Customer profile: {customer_profile}\n"
            f"Product: {product}\n"
            f"Trend summary: {trend_summary}"
        )
        text = self._ai_logging_service.call_with_logging(
            step_name="ad_copy",
            model_name=self._settings.openai_deployment,
            ai_input_raw=prompt,
            logged_in_user_identity=user_identity,
            callback=lambda: invoke_model(self._settings, prompt),
        )
        words = text.split()
        if len(words) > 500:
            text = " ".join(words[:500])
        return {"ad_copy_text": text, "generated_at": datetime.now(UTC)}
