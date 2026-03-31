from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status


class HistoryQueryValidator:
    @staticmethod
    def validate(user_id: str | None, session_id: str | None, generation_id: str | None) -> tuple[str | None, str | None, UUID | None]:
        if not any([user_id, session_id, generation_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='One of userId, sessionId, or generationId is required',
            )

        parsed_generation_id = None
        if generation_id:
            try:
                parsed_generation_id = UUID(generation_id)
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid generationId format') from exc

        return (user_id.strip() if user_id else None, session_id.strip() if session_id else None, parsed_generation_id)
