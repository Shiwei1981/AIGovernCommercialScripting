from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from app.config import Settings
from app.data.repositories.ai_generation_log_repository import AIGenerationLogRepository


class AILoggingService:
    def __init__(self, settings: Settings, repository: AIGenerationLogRepository):
        self._settings = settings
        self._repository = repository

    def call_with_logging(
        self,
        *,
        step_name: str,
        model_name: str,
        ai_input_raw: str,
        logged_in_user_identity: str,
        callback: Callable[[], str],
    ) -> str:
        correlation_id = str(uuid4())
        api_identity = self._settings.azure_client_id
        try:
            output = callback()
            self._repository.save(
                step_name=step_name,
                model_name=model_name,
                ai_input_raw=ai_input_raw,
                ai_output_raw=output,
                execution_status="success",
                execution_error=None,
                api_execution_identity=api_identity,
                logged_in_user_identity=logged_in_user_identity,
                correlation_id=correlation_id,
            )
            return output
        except Exception as exc:
            self._repository.save(
                step_name=step_name,
                model_name=model_name,
                ai_input_raw=ai_input_raw,
                ai_output_raw="",
                execution_status="failure",
                execution_error=str(exc),
                api_execution_identity=api_identity,
                logged_in_user_identity=logged_in_user_identity,
                correlation_id=correlation_id,
            )
            raise
