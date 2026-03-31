from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.dependencies.auth import AuthenticatedUser, get_current_user
from src.models.api import AuditTraceResponse
from src.repositories.audit_trace_repository import AuditTraceRepository
from src.services.audit_event_service import AuditEventService

router = APIRouter(tags=['Audit'])


@router.get('/generations/{generation_id}/audit', response_model=AuditTraceResponse, response_model_exclude_none=True)
def get_audit_trace(generation_id: UUID, request: Request, user: AuthenticatedUser = Depends(get_current_user)):
    trace = AuditTraceRepository().get_trace(generation_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Generation not found')

    AuditEventService().emit(
        user_id=user.user_id,
        session_id='n/a',
        action_type='audit_viewed',
        action_status='success',
        request_correlation_id=request.state.correlation_id,
        generation_id=generation_id,
    )
    return trace
