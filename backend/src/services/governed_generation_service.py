from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.models.api import GenerationCreateRequest
from src.models.contracts import GenerationRecord
from src.repositories.generation_repository import GenerationRepository
from src.services.audit_event_service import AuditEventService
from src.services.openai_generation_service import OpenAIGenerationService
from src.services.search_retrieval_service import SearchRetrievalService
from src.config.settings import get_settings


class GovernedGenerationService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._generation_repository = GenerationRepository()
        self._retrieval_service = SearchRetrievalService()
        self._openai_service = OpenAIGenerationService()
        self._audit_service = AuditEventService()

    async def create_generation(self, request: GenerationCreateRequest, user_id: str, user_display_name: str | None, correlation_id: str):
        generation_id = uuid4()
        created_at = datetime.now(timezone.utc)

        references = self._retrieval_service.retrieve_recent(request.prompt, generation_id) if request.use_recent_news else []
        grounding_mode = 'news' if references else 'none'

        self._audit_service.emit(
            user_id=user_id,
            session_id=request.session_id,
            action_type='generation_requested',
            action_status='success',
            request_correlation_id=correlation_id,
            generation_id=generation_id,
        )

        response_text, used_rest_fallback = await self._openai_service.generate(
            request.prompt,
            [source.excerpt_text or source.source_title for source in references],
        )

        generation = GenerationRecord(
            generationId=generation_id,
            sessionId=request.session_id,
            userId=user_id,
            userDisplayName=user_display_name,
            promptText=request.prompt,
            responseText=response_text,
            status='completed',
            groundingMode=grounding_mode,
            modelDeployment=self._settings.azure_openai_deployment,
            usedRestFallback=used_rest_fallback,
            createdAtUtc=created_at,
            completedAtUtc=datetime.now(timezone.utc),
            requestCorrelationId=correlation_id,
            sourceReferences=references,
        )
        self._generation_repository.save_generation(generation)

        self._audit_service.emit(
            user_id=user_id,
            session_id=request.session_id,
            action_type='generation_completed',
            action_status='success',
            request_correlation_id=correlation_id,
            generation_id=generation_id,
            details={'sourceCount': len(references)},
        )

        return generation
