# Governance Requirements Checklist: Governed Script Workflow

**Purpose**: Validate the completeness, clarity, consistency, and measurability of the governed workflow requirements across the feature spec, plan, data model, and shared contracts before task execution.
**Created**: 2026-03-31
**Feature**: [spec.md](../spec.md), [plan.md](../plan.md), [data-model.md](../data-model.md), [contracts](../contracts)

**Note**: This checklist tests the quality of the written requirements and planning artifacts. It does not verify implementation behavior.

## Requirement Completeness

- [X] CHK001 Are authentication requirements fully specified for every user-facing entry point, including sign-in preconditions, authorized access boundaries, and the absence of anonymous flows? [Completeness, Spec §FR-001, Spec §User Story 1, Plan §Constitution Check]
- [X] CHK002 Are the governed generation requirements complete for both grounded and ungrounded outcomes, including when recent-news context is applied and when it is intentionally withheld? [Completeness, Spec §FR-002, Spec §FR-003, Spec §FR-004, Spec §FR-010]
- [X] CHK003 Are persistence requirements fully defined for generation history, source references, and audit evidence so that user, session, and generation lookups are all covered without relying on implicit behavior? [Completeness, Spec §FR-005, Spec §FR-006, Spec §FR-007, Schema generation-record.schema.json, Schema audit-record.schema.json]
- [X] CHK004 Are the database-boundary requirements complete about which new SQL objects are allowed, which existing tables are immutable, and which retrieval surfaces depend on read-only views? [Completeness, Spec §FR-009, Spec §FR-013, Plan §Technical Context, Data Model §SQL Object Boundaries]

## Requirement Clarity

- [X] CHK005 Is the six-month freshness rule defined precisely enough that reviewers can tell whether publication date, ingestion date, or retrieval date is the decisive criterion for eligibility? [Clarity, Spec §FR-003, Spec §FR-014, Data Model §NewsIndexDocument]
- [X] CHK006 Is the phrase "controlled failure path" clarified with objective expectations for user-visible response content, audit capture, and persistence outcomes across retrieval and generation failures? [Clarity, Spec §FR-010, Spec §Edge Cases, Contract openapi.yaml /api/generations]
- [X] CHK007 Are the history-search requirements specific about whether searches may combine user ID, session ID, and generation ID filters, and how ambiguous or over-broad queries should be handled? [Clarity, Spec §FR-006, Contract openapi.yaml /api/generations GET, Gap]
- [X] CHK008 Is the requirement to preserve authoritative shared contracts explicit enough about which fields are mandatory for downstream correlation versus optional enrichment data? [Clarity, Spec §FR-008, Schema generation-record.schema.json, Schema audit-record.schema.json]

## Requirement Consistency

- [X] CHK009 Do the specification and contract artifacts define the same lifecycle states for generation outcomes without conflict or omission? [Consistency, Spec §FR-010, Contract openapi.yaml GenerationCreateResponse.status, Schema generation-record.schema.json status]
- [X] CHK010 Are audit-action requirements consistent between the feature spec, API contract, and audit schema for sign-in, generation, history search, and evidence review events? [Consistency, Spec §FR-007, Contract openapi.yaml /api/generations/{generationId}/audit, Schema audit-record.schema.json]
- [X] CHK011 Do the persistence boundaries remain consistent across the spec, plan, and data model about append-only tables, dedicated schema usage, and read-only retrieval views? [Consistency, Spec §FR-013, Plan §Summary, Data Model §SQL Object Boundaries]
- [X] CHK012 Are the LangChain exclusion and direct Azure OpenAI SDK requirements stated consistently across the feature requirements, assumptions, and planning materials without leaving a contradictory fallback path? [Consistency, Spec §FR-011, Spec §FR-012, Spec §Assumptions, Plan §Phase 0 Research Summary]

## Acceptance Criteria Quality

- [X] CHK013 Are success criteria measurable enough to determine whether sign-in, grounded generation, searchable history retrieval, and audit traceability are acceptable without subjective interpretation? [Acceptance Criteria, Spec §SC-001, Spec §SC-002, Spec §SC-003, Spec §SC-004]
- [X] CHK014 Do the written acceptance outcomes define what counts as a "valid" source URL, "correct" history record, and "reliable" cross-project linkage so that reviewers can evaluate the criteria objectively? [Measurability, Spec §SC-002, Spec §SC-003, Spec §SC-004, Ambiguity]
- [X] CHK015 Are documentation-validation requirements defined as verifiable gates with explicit completion conditions for Azure OpenAI, Entra, Azure AI Search, Azure SQL, and the LangChain non-adoption decision? [Acceptance Criteria, Spec §SC-005, Plan §Testing, Gap]

## Scenario Coverage

- [X] CHK016 Are requirements documented for all primary scenarios: authenticated generation, search by user ID, search by session ID, search by generation ID, and audit trace review? [Coverage, Spec §User Story 1, Spec §User Story 2, Spec §User Story 3, Contract openapi.yaml]
- [X] CHK017 Are alternate-path requirements defined for valid requests that do not use recent-news grounding, including what evidence must still be stored and returned? [Coverage, Spec §FR-002, Spec §FR-005, Schema generation-record.schema.json, Gap]
- [X] CHK018 Are recovery-path requirements defined for partial failures such as successful retrieval but failed generation, or persisted generation with failed audit-write follow-up? [Coverage, Spec §FR-010, Spec §Edge Cases, Data Model §State Transitions, Gap]

## Edge Case Coverage

- [X] CHK019 Are edge-case requirements complete for missing source metadata, expired articles, unsupported documentation paths, and feature requests that would require existing-table changes? [Edge Case Coverage, Spec §Edge Cases, Spec §FR-009, Spec §FR-014]
- [X] CHK020 Is the specification explicit about what should happen when a search request supplies no supported key, multiple keys, or identifiers that do not resolve to any record? [Edge Case Coverage, Contract openapi.yaml /api/generations GET, Gap]
- [X] CHK021 Are deployment-exception requirements defined for certificate trust, DNS binding, and consent steps strongly enough that reviewers can distinguish acceptable manual exceptions from missing deployment requirements? [Edge Case Coverage, Spec §Edge Cases, Plan §Constraints, Plan §Phase 1 Design Summary]

## Non-Functional Requirements

- [X] CHK022 Are security and secret-handling requirements explicitly specified for environment-variable inputs, managed identity use, token boundaries, and the prohibition on embedded credentials? [Non-Functional Requirements, Spec §Constitution Alignment, Spec §Assumptions, Plan §Technical Context]
- [X] CHK023 Are deployment requirements explicit that native ARM JSON is the artifact standard and that VM-hosted HTTPS assumptions are part of the governed scope rather than informal implementation notes? [Non-Functional Requirements, Spec §Constitution Alignment, Plan §Summary, Plan §Project Structure]
- [X] CHK024 Are performance and timing expectations written at the requirement level strongly enough to support reviewer judgment for demo-scale search latency, generation completion, and ingestion freshness maintenance? [Non-Functional Requirements, Plan §Technical Context, Gap]

## Dependencies And Assumptions

- [X] CHK025 Are external dependency assumptions documented for the allowlisted corpus, Entra app registration, Azure OpenAI deployment, Azure AI Search indexing cadence, and Azure SQL access model? [Dependencies, Spec §Assumptions, Plan §Technical Context, Data Model §NewsIndexDocument]
- [X] CHK026 Are the repo bootstrap and environment-variable expectations defined completely enough that a reviewer can tell which tenant, client, endpoint, deployment, search, SQL, and certificate inputs are mandatory? [Dependencies, Plan §Phase 1 Design Summary, Gap]

## Ambiguities And Conflicts

- [X] CHK027 Is it unambiguous whether generation history retrieval is limited to operators or also available to ordinary end users with their own records? [Ambiguity, Spec §User Story 2, Spec §FR-006]
- [X] CHK028 Do the requirements clearly separate user-facing application obligations from downstream governance-consumer obligations so contract sufficiency does not depend on unstated responsibilities in other projects? [Conflict, Spec §User Story 3, Spec §FR-008, Spec §Constitution Alignment]

## Notes

- Use this checklist during PR review of the feature documents before task generation or implementation changes proceed.
- Record findings inline next to the checklist item when a requirement gap or ambiguity is discovered.