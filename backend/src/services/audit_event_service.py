from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.config.settings import get_settings
from src.models.contracts import AuditRecord
from src.repositories.audit_repository import AuditRepository


class AuditEventService:
    def __init__(self, audit_repository: AuditRepository | None = None) -> None:
        self._settings = get_settings()
        self._audit_repository = audit_repository or AuditRepository()

    def emit(
        self,
        *,
        user_id: str,
        session_id: str,
        action_type: str,
        action_status: str,
        request_correlation_id: str,
        generation_id: UUID | None = None,
        details: dict | None = None,
    ) -> AuditRecord:
        event = AuditRecord(
            auditEventId=uuid4(),
            generationId=generation_id,
            sessionId=session_id,
            userId=user_id,
            actionType=action_type,
            actionStatus=action_status,
            occurredAtUtc=datetime.now(timezone.utc),
            requestCorrelationId=request_correlation_id,
            clientAppId=self._settings.entra_client_id,
            details=details or {},
        )
        return self._audit_repository.append(event)
