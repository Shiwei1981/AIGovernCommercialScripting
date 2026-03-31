from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.auth import get_current_user
from src.models.contracts import GenerationRecord
from src.repositories.generation_repository import GenerationRepository

router = APIRouter(tags=['Generations'])


@router.get('/generations/{generation_id}', response_model=GenerationRecord, response_model_exclude_none=True)
def get_generation_detail(generation_id: UUID, _=Depends(get_current_user)):
    generation = GenerationRepository().get_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Generation not found')
    return generation
