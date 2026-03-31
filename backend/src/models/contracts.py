from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


GenerationStatus = Literal['received', 'grounded', 'completed', 'failed']
GroundingMode = Literal['news', 'none', 'fallback']
AuditActionType = Literal[
    'sign_in',
    'generation_requested',
    'generation_completed',
    'generation_failed',
    'history_searched',
    'audit_viewed',
]
AuditActionStatus = Literal['success', 'failure']


class SourceReference(BaseModel):
    source_reference_id: UUID = Field(alias='sourceReferenceId')
    generation_id: UUID = Field(alias='generationId')
    source_title: str = Field(alias='sourceTitle')
    canonical_url: str = Field(alias='canonicalUrl')
    published_at_utc: datetime = Field(alias='publishedAtUtc')
    freshness_eligible: bool = Field(alias='freshnessEligible')
    excerpt_text: str | None = Field(default=None, alias='excerptText')


class GenerationRecord(BaseModel):
    generation_id: UUID = Field(alias='generationId')
    session_id: str = Field(alias='sessionId')
    user_id: str = Field(alias='userId')
    status: GenerationStatus
    grounding_mode: GroundingMode = Field(alias='groundingMode')
    model_deployment: str = Field(alias='modelDeployment')
    used_rest_fallback: bool = Field(alias='usedRestFallback')
    created_at_utc: datetime = Field(alias='createdAtUtc')
    request_correlation_id: str = Field(alias='requestCorrelationId')
    user_display_name: str | None = Field(default=None, alias='userDisplayName')
    prompt_text: str | None = Field(default=None, alias='promptText')
    response_text: str | None = Field(default=None, alias='responseText')
    failure_reason: str | None = Field(default=None, alias='failureReason')
    completed_at_utc: datetime | None = Field(default=None, alias='completedAtUtc')
    source_references: list[SourceReference] = Field(default_factory=list, alias='sourceReferences')


class AuditRecord(BaseModel):
    audit_event_id: UUID = Field(alias='auditEventId')
    generation_id: UUID | None = Field(default=None, alias='generationId')
    session_id: str = Field(alias='sessionId')
    user_id: str = Field(alias='userId')
    action_type: AuditActionType = Field(alias='actionType')
    action_status: AuditActionStatus = Field(alias='actionStatus')
    occurred_at_utc: datetime = Field(alias='occurredAtUtc')
    request_correlation_id: str = Field(alias='requestCorrelationId')
    client_app_id: str = Field(alias='clientAppId')
    client_ip_hash: str | None = Field(default=None, alias='clientIpHash')
    details: dict[str, object] | None = None
