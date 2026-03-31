from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies.auth import AuthenticatedUser, get_current_user
from src.models.api import GenerationHistoryResponse
from src.repositories.history_repository import HistoryRepository
from src.services.history_query_validator import HistoryQueryValidator
from src.services.audit_event_service import AuditEventService

router = APIRouter(tags=['Generations'])


@router.get('/generations', response_model=GenerationHistoryResponse)
def search_generations(
    userId: str | None = None,
    sessionId: str | None = None,
    generationId: str | None = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    parsed_user_id, parsed_session_id, parsed_generation_id = HistoryQueryValidator.validate(
        userId,
        sessionId,
        generationId,
    )

    items = HistoryRepository().search(
        user_id=parsed_user_id,
        session_id=parsed_session_id,
        generation_id=parsed_generation_id,
    )

    AuditEventService().emit(
        user_id=user.user_id,
        session_id=parsed_session_id or 'n/a',
        action_type='history_searched',
        action_status='success',
        request_correlation_id='history-search',
        details={'resultCount': len(items)},
    )
    return GenerationHistoryResponse(items=items)
