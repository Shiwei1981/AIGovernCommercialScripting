from __future__ import annotations

from uuid import UUID

from src.models.contracts import AuditRecord

_AUDIT_EVENTS: list[AuditRecord] = []


class AuditRepository:
    def append(self, event: AuditRecord) -> AuditRecord:
        _AUDIT_EVENTS.append(event)
        return event

    def list_by_generation(self, generation_id: UUID) -> list[AuditRecord]:
        return [event for event in _AUDIT_EVENTS if event.generation_id == generation_id]

    def list_by_identity(self, user_id: str, session_id: str | None = None) -> list[AuditRecord]:
        items = [event for event in _AUDIT_EVENTS if event.user_id == user_id]
        if session_id:
            items = [event for event in items if event.session_id == session_id]
        return items
