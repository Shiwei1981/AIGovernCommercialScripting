from __future__ import annotations

from uuid import UUID

from src.models.api import AuditTraceResponse
from src.repositories.audit_repository import AuditRepository
from src.repositories.generation_repository import GenerationRepository


class AuditTraceRepository:
    def __init__(
        self,
        generation_repository: GenerationRepository | None = None,
        audit_repository: AuditRepository | None = None,
    ) -> None:
        self._generation_repository = generation_repository or GenerationRepository()
        self._audit_repository = audit_repository or AuditRepository()

    def get_trace(self, generation_id: UUID) -> AuditTraceResponse | None:
        generation = self._generation_repository.get_generation(generation_id)
        if generation is None:
            return None

        events = self._audit_repository.list_by_generation(generation_id)
        return AuditTraceResponse(
            generationId=generation_id,
            auditEvents=events,
            sourceReferences=generation.source_references,
        )
