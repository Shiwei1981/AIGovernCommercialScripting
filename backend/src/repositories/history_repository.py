from __future__ import annotations

from uuid import UUID

from src.models.api import GenerationHistoryItem
from src.repositories.generation_repository import GenerationRepository


class HistoryRepository:
    def __init__(self, generation_repository: GenerationRepository | None = None) -> None:
        self._generation_repository = generation_repository or GenerationRepository()

    def search(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        generation_id: UUID | None = None,
    ) -> list[GenerationHistoryItem]:
        generations = self._generation_repository.all_generations()
        filtered = []
        for record in generations:
            if user_id and record.user_id != user_id:
                continue
            if session_id and record.session_id != session_id:
                continue
            if generation_id and record.generation_id != generation_id:
                continue
            filtered.append(
                GenerationHistoryItem(
                    generationId=record.generation_id,
                    sessionId=record.session_id,
                    userId=record.user_id,
                    status=record.status,
                    createdAtUtc=record.created_at_utc,
                    completedAtUtc=record.completed_at_utc,
                    sourceCount=len(record.source_references),
                )
            )
        return sorted(filtered, key=lambda item: item.created_at_utc, reverse=True)
