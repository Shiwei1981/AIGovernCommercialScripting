from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.dependencies import get_auth_service
from app.models.contracts import SessionState, UserInfo
from app.services.entra_auth_service import EntraAuthService

router = APIRouter(prefix="/api", tags=["session"])


@router.get("/session", response_model=SessionState)
def session_state(
    request: Request,
    auth_service: EntraAuthService = Depends(get_auth_service),
) -> SessionState:
    user = auth_service.get_optional_user(request)
    if not user:
        return SessionState(authenticated=False, user=None)
    return SessionState(authenticated=True, user=UserInfo(**user))
