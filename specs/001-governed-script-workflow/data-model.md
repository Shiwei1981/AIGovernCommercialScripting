# Data Model: Governed Script Workflow

## Overview

The feature persists governed generation evidence in new append-only SQL objects and exposes retrieval through read-only views. The data model keeps generation identity, source evidence, and audit traceability explicit so downstream governance consumers can correlate records reliably.

## Entities

### GenerationRecord

- **Purpose**: Canonical stored record for a governed generation request and its resulting output.
- **Storage**: Table `governance_history.generation_record`
- **Fields**:
  - `generation_id` (UUID, required, primary key)
  - `session_id` (string, required, indexed)
  - `user_id` (string, required, indexed)
  - `user_display_name` (string, optional)
  - `prompt_text` (string, required)
  - `response_text` (string, optional until completion)
  - `generation_status` (enum: `received`, `grounded`, `completed`, `failed`, required)
  - `grounding_mode` (enum: `news`, `none`, `fallback`, required)
  - `model_deployment` (string, required)
  - `used_rest_fallback` (boolean, required, default `false`)
  - `failure_reason` (string, optional)
  - `created_at_utc` (datetime, required)
  - `completed_at_utc` (datetime, optional)
  - `request_correlation_id` (string, required)
- **Validation rules**:
  - `prompt_text` must be non-empty after trimming.
  - `response_text` is required when `generation_status` is `completed`.
  - `failure_reason` is required when `generation_status` is `failed`.
  - `completed_at_utc` must be greater than or equal to `created_at_utc`.

### SourceReference

- **Purpose**: Evidence record tying a generated output to one retrieved article.
- **Storage**: Table `governance_history.source_reference`
- **Fields**:
  - `source_reference_id` (UUID, required, primary key)
  - `generation_id` (UUID, required, foreign key to `generation_record`)
  - `search_document_id` (string, required)
  - `source_title` (string, required)
  - `canonical_url` (string, required)
  - `published_at_utc` (datetime, required)
  - `retrieved_at_utc` (datetime, required)
  - `freshness_eligible` (boolean, required)
  - `search_score` (number, optional)
  - `excerpt_text` (string, optional)
  - `source_rank` (integer, required)
- **Validation rules**:
  - `canonical_url` must be an HTTPS URL.
  - `freshness_eligible` must be `true` for references attached to grounded responses.
  - `published_at_utc` must be within six months of `retrieved_at_utc` for grounded responses.

### AuditRecord

- **Purpose**: Append-only trace event for identity, generation, retrieval, and evidence access actions.
- **Storage**: Table `governance_history.audit_record`
- **Fields**:
  - `audit_event_id` (UUID, required, primary key)
  - `generation_id` (UUID, optional, foreign key to `generation_record`)
  - `session_id` (string, required, indexed)
  - `user_id` (string, required, indexed)
  - `action_type` (enum: `sign_in`, `generation_requested`, `generation_completed`, `generation_failed`, `history_searched`, `audit_viewed`, required)
  - `action_status` (enum: `success`, `failure`, required)
  - `occurred_at_utc` (datetime, required)
  - `request_correlation_id` (string, required)
  - `client_app_id` (string, required)
  - `client_ip_hash` (string, optional)
  - `details_json` (JSON string, optional)
- **Validation rules**:
  - `generation_id` is required for generation and audit-view events.
  - `details_json` must not contain secrets or raw tokens.
  - Records are append-only and must never be updated in place.

### NewsIndexDocument

- **Purpose**: Azure AI Search document representing one allowlisted article.
- **Storage**: Azure AI Search index `commercialscripting-news`
- **Fields**:
  - `document_id` (string, required, key)
  - `allowlist_source` (string, required, filterable)
  - `canonical_url` (string, required)
  - `title` (string, required, searchable)
  - `summary_text` (string, optional, searchable)
  - `body_text` (string, optional, searchable)
  - `published_at_utc` (datetimeoffset, required, filterable and sortable)
  - `ingested_at_utc` (datetimeoffset, required)
  - `content_hash` (string, required)
  - `source_language` (string, optional)
- **Validation rules**:
  - `published_at_utc` must be normalized to UTC.
  - `canonical_url` and `allowlist_source` are required before indexing.
  - Documents older than six months are excluded from grounding queries.

### GenerationHistoryView

- **Purpose**: Read-only projection used for history retrieval by user ID, session ID, or generation ID.
- **Storage**: View `governance_history.vw_generation_history_search`
- **Fields**:
  - `generation_id`
  - `session_id`
  - `user_id`
  - `generation_status`
  - `created_at_utc`
  - `completed_at_utc`
  - `source_count`
  - `last_audit_status`
- **Validation rules**:
  - The view is read-only and sourced only from the new append-only tables.

### AuditTraceView

- **Purpose**: Read-only projection used to reconstruct evidence for reviewers and downstream consumers.
- **Storage**: View `governance_history.vw_generation_audit_trace`
- **Fields**:
  - `generation_id`
  - `session_id`
  - `user_id`
  - `audit_event_id`
  - `action_type`
  - `action_status`
  - `occurred_at_utc`
  - `canonical_url`
  - `published_at_utc`
- **Validation rules**:
  - Every row must resolve to one persisted audit record.
  - Rows are derived only from append-only tables and source references.

## Relationships

- `GenerationRecord` 1-to-many `SourceReference`
- `GenerationRecord` 1-to-many `AuditRecord`
- `GenerationRecord` and `AuditRecord` are grouped by `session_id` and `user_id`
- `NewsIndexDocument` is referenced by `SourceReference.search_document_id`
- `GenerationHistoryView` aggregates `GenerationRecord`, `SourceReference`, and `AuditRecord`
- `AuditTraceView` joins `GenerationRecord`, `AuditRecord`, and `SourceReference`

## State Transitions

### GenerationRecord

- `received` -> `grounded`: retrieval returned compliant allowlisted evidence.
- `received` -> `completed`: generation completed without external grounding.
- `grounded` -> `completed`: response was generated with retained source references.
- `received` -> `failed`: request failed before or during generation.
- `grounded` -> `failed`: generation or persistence failed after retrieval.

### NewsIndexDocument

- `staged` -> `indexed`: article passed allowlist, canonical URL, and publication-date validation.
- `indexed` -> `expired`: article is older than six months and excluded from grounding queries.
- `indexed` -> `reindexed`: article content or metadata was refreshed by scheduled ingestion.

## SQL Object Boundaries

- New schema: `governance_history`
- New tables: `generation_record`, `source_reference`, `audit_record`
- New views: `vw_generation_history_search`, `vw_generation_audit_trace`
- Existing tables in `aigovernadvworksdb` remain unchanged and are not referenced for writes.