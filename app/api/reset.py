from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import require_user
from app.models.contracts import ResetResponse

router = APIRouter(prefix="/api", tags=["reset"])


@router.post("/reset", response_model=ResetResponse)
def reset(_: dict = Depends(require_user)) -> ResetResponse:
    return ResetResponse(status="ok", message="Flow state has been reset.")
