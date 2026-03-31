from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from src.api.dependencies.auth import AuthenticatedUser, get_current_user
from src.models.api import GenerationCreateRequest, GenerationCreateResponse
from src.services.governed_generation_service import GovernedGenerationService

router = APIRouter(tags=['Generations'])


@router.post(
    '/generations',
    response_model=GenerationCreateResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_generation(
    payload: GenerationCreateRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    service = GovernedGenerationService()
    generation = await service.create_generation(
        payload,
        user_id=user.user_id,
        user_display_name=user.display_name,
        correlation_id=request.state.correlation_id,
    )
    return GenerationCreateResponse(
        generationId=generation.generation_id,
        status=generation.status,
        createdAtUtc=generation.created_at_utc,
        responseText=generation.response_text,
        sourceReferences=generation.source_references,
        failureReason=generation.failure_reason,
    )
