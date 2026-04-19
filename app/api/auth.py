from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.dependencies import get_auth_service
from app.services.entra_auth_service import EntraAuthService

router = APIRouter(tags=["auth"])


@router.get("/auth/login", status_code=302)
def login(auth_service: EntraAuthService = Depends(get_auth_service)):
    return RedirectResponse(url=auth_service.login_redirect_url(), status_code=302)


@router.get("/auth/callback", status_code=302)
def callback(
    code: str | None = None,
    mock_user: str | None = Query(default=None),
    auth_service: EntraAuthService = Depends(get_auth_service),
):
    user = auth_service.process_callback(code=code, mock_user=mock_user)
    session_id = auth_service.create_session(user)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return response
