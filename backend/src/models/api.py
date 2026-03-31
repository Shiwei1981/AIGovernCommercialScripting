from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.contracts import AuditRecord, GenerationRecord, SourceReference


class GenerationCreateRequest(BaseModel):
    session_id: str = Field(alias='sessionId', min_length=1)
    prompt: str = Field(min_length=1)
    use_recent_news: bool = Field(default=True, alias='useRecentNews')


class GenerationCreateResponse(BaseModel):
    generation_id: UUID = Field(alias='generationId')
    status: str
    created_at_utc: datetime = Field(alias='createdAtUtc')
    response_text: str | None = Field(default=None, alias='responseText')
    source_references: list[SourceReference] = Field(default_factory=list, alias='sourceReferences')
    failure_reason: str | None = Field(default=None, alias='failureReason')


class GenerationHistoryItem(BaseModel):
    generation_id: UUID = Field(alias='generationId')
    session_id: str = Field(alias='sessionId')
    user_id: str = Field(alias='userId')
    status: str
    created_at_utc: datetime = Field(alias='createdAtUtc')
    completed_at_utc: datetime | None = Field(default=None, alias='completedAtUtc')
    source_count: int = Field(alias='sourceCount')


class GenerationHistoryResponse(BaseModel):
    items: list[GenerationHistoryItem]


class AuditTraceResponse(BaseModel):
    generation_id: UUID = Field(alias='generationId')
    audit_events: list[AuditRecord] = Field(alias='auditEvents')
    source_references: list[SourceReference] = Field(alias='sourceReferences')


class GenerationDetailResponse(BaseModel):
    generation: GenerationRecord
