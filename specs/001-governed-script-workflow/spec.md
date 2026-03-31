# Feature Specification: Governed Script Workflow

**Feature Branch**: `001-governed-script-workflow`  
**Created**: 2026-03-31  
**Status**: Draft  
**Input**: User description: "Create CommercialScripting governed generation workflow with Entra sign-in, recent-news grounding, Azure SQL history search, and audit traceability"

## Clarifications

### Session 2026-03-31

- Q: What exact Entra sign-in flow and redirect URI pattern best fit the VM-hosted HTML5 app? → A: Browser-based Entra sign-in using authorization code with PKCE via MSAL.js, with an HTTPS callback path such as `/auth/callback` on the app domain.
- Q: Which generation integration path should be treated as primary after documentation validation? → A: Use the direct Azure OpenAI SDK as the primary generation path, with REST as fallback if SDK validation hits a documented gap.
- Q: Which new SQL objects are allowed for history and audit persistence without touching existing tables? → A: Allow new append-only tables for generation history and audit records in a dedicated schema, plus read-only views for search and downstream consumption.
- Q: Which Azure AI Search indexing and refresh mechanism will guarantee six-month freshness and source URLs for the allowlisted corpus? → A: Use a scheduled ingestion job that pulls only allowlisted news sources, normalizes canonical article URL and publish date, and reindexes Azure AI Search on a fixed cadence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit a Governed Generation Request (Priority: P1)

An authenticated business user signs in, enters a prompt, and receives a generated commercial script that is grounded in recent allowlisted news sources when relevant.

**Why this priority**: This is the primary product outcome and the source of all downstream history and audit evidence.

**Independent Test**: Can be fully tested by signing in as an authorized user, submitting a valid request, and verifying that the returned output includes grounded content with source references when recent-news context is used.

**Acceptance Scenarios**:

1. **Given** an authorized user is not signed in, **When** the user accesses the application and completes sign-in, **Then** the user reaches the governed script-generation experience without accessing any anonymous workflow.
2. **Given** an authorized user submits a valid prompt that benefits from recent-news context, **When** the request is processed, **Then** the system returns a generated response with the supporting source references and article links used for grounding.
3. **Given** a request cannot be grounded with compliant recent-news sources, **When** the system completes processing, **Then** it returns a controlled response that explains the limitation and does not fabricate unsupported citations.

---

### User Story 2 - Retrieve Generation History (Priority: P2)

An end user or operator searches prior generations using a user identifier, session identifier, or generation identifier and retrieves the matching record set with enough context to understand what happened.

**Why this priority**: History retrieval is required for user follow-up, operational support, and compliance evidence without depending on downstream systems.

**Independent Test**: Can be fully tested by creating stored generations and then verifying that searches by each supported identifier return the expected records and associated context.

**Acceptance Scenarios**:

1. **Given** stored generation records exist for multiple users and sessions, **When** an operator searches by user ID, **Then** the system returns only the matching generation history for that user.
2. **Given** stored generation records exist within a session, **When** an operator searches by session ID, **Then** the system returns the generation set associated with that session.
3. **Given** a known generation ID exists, **When** an operator searches for that generation ID, **Then** the system returns the matching generation record with its source references and audit context.

---

### User Story 3 - Trace Governance Evidence (Priority: P3)

A governance reviewer inspects a generated result and traces it back to the generation identity, source references, and audit events needed for downstream cross-project correlation.

**Why this priority**: Audit traceability is essential for governance confidence, downstream portfolio integration, and acceptance readiness.

**Independent Test**: Can be fully tested by selecting a stored generation and verifying that its identity, source references, and audit trail are sufficient to reconstruct who generated it, in which session, and with which evidence.

**Acceptance Scenarios**:

1. **Given** a stored governed output exists, **When** a reviewer opens its details, **Then** the system shows the generation identity, user context, session context, and source references needed for traceability.
2. **Given** a downstream governance consumer reads the generation and audit outputs, **When** it correlates records across projects, **Then** the identifiers and audit fields are sufficient for reliable cross-project linkage.

### Edge Cases

- A requested generation topic has no allowlisted news sources that meet the six-month freshness rule.
- Search results contain missing or incomplete source metadata from an upstream retrieval dependency.
- Documentation validation shows a planned orchestration path no longer matches official service guidance.
- A proposed enhancement would require changing an existing database table.
- Certificate trust or hostname configuration limits access to approved demo environments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require authenticated organizational sign-in before any user can access the script-generation workflow, using Entra authorization code with PKCE from the HTML5 client.
- **FR-002**: The system MUST allow an authenticated user to submit a prompt and receive a governed generated response through the primary application experience.
- **FR-003**: The system MUST enrich eligible generation requests with recent-news context only from approved sources that include canonical article URLs and meet the six-month freshness rule.
- **FR-004**: The system MUST return source references for any response that uses recent-news context and MUST avoid presenting unsupported or fabricated citations.
- **FR-005**: The system MUST persist each generation request and response as retrievable history with generation identity, user context, and session context.
- **FR-006**: The system MUST support retrieval of stored generation history by user ID, session ID, and generation ID.
- **FR-007**: The system MUST create audit records for sign-in, generation, and retrieval actions that are sufficient for downstream governance correlation.
- **FR-008**: The system MUST preserve authoritative shared generation identity and audit-record contracts for downstream consumers.
- **FR-009**: The system MUST reject or block feature behavior that would require modification of existing database tables unless the scope is formally redefined before implementation.
- **FR-010**: The system MUST provide a controlled failure path when recent-news retrieval, generation validation, or persistence cannot complete while preserving audit traceability.
- **FR-011**: The system MUST use the direct Azure OpenAI SDK as the primary generation path and MUST document a direct REST fallback if SDK validation reveals a documented compatibility gap.
- **FR-012**: The system MUST treat LangChain as out of scope for implementation unless a later amendment explicitly re-approves it after documentation validation.
- **FR-013**: The system MUST persist generation history and audit records only in new append-only tables within a dedicated database schema and MUST expose retrieval and downstream read access through read-only views.
- **FR-014**: The system MUST populate Azure AI Search through a scheduled ingestion job that admits only allowlisted news articles, normalizes canonical source URLs and publication dates at ingestion time, and reindexes on a fixed cadence that preserves the six-month freshness guarantee.

### Key Entities *(include if feature involves data)*

- **Generation Request**: A user-submitted instruction with the user identity, session identity, request time, and any retrieval context used to produce a governed output.
- **Generation Record**: A stored result containing the generation identifier, generated content, associated source references, status, and timestamps required for history retrieval.
- **Audit Record**: A trace event describing who performed an action, what action occurred, when it occurred, and which generation or session it relates to.
- **Source Reference**: A citation artifact containing the source title, source URL, freshness eligibility, and relationship to a generated output.
- **Governance History Schema**: A dedicated append-only SQL schema that contains the new generation-history and audit tables plus read-only views used for retrieval and downstream consumption.
- **Allowlisted News Index**: The Azure AI Search index populated by a scheduled ingestion process that stores only allowlisted articles with canonical source URLs, publication dates, and the metadata needed to enforce the six-month freshness rule.

## Constitution Alignment *(mandatory)*

- **Authentication Boundary**: All user-facing access is restricted to Entra ID sign-in using the CommercialScripting-owned app registration. The HTML5 client uses authorization code with PKCE via MSAL.js and an HTTPS callback path on the application domain such as `/auth/callback`. No anonymous or alternate consumer sign-in path is permitted for this feature.
- **Runtime Boundary**: The experience is bounded to an HTML5 frontend and a stateless Python backend delivered over HTTPS on the CommercialScripting VM baseline. Secrets and connection values must come from secure runtime configuration rather than embedded credentials.
- **Contracts and Data Boundary**: Generation identity and audit records remain the authoritative shared contracts for downstream governance projects. Existing tables in `aigovernadvworksdb` remain unchanged; persistence is limited to new append-only tables in a dedicated schema plus read-only views for retrieval and downstream consumption.
- **Retrieval Boundary**: News grounding is limited to the allowlisted internet-news corpus, must retain canonical source URLs, and must enforce six-month freshness. Azure AI Search content must be populated by a scheduled ingestion job that normalizes source URLs and publication dates before fixed-cadence reindexing. The direct Azure OpenAI SDK is the required primary generation path, and a direct REST path is the only approved fallback if SDK validation identifies a documented gap.
- **Deployment and Evidence Boundary**: Deployment planning must continue to target native ARM JSON artifacts, and any manual VM certificate or hostname steps must be documented. Acceptance evidence must show sign-in, grounded generation, persisted history, searchable retrieval, and audit traceability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of authorized users in acceptance testing can sign in and complete a valid script-generation request without manual operator intervention.
- **SC-002**: At least 95% of successful grounded responses presented in acceptance testing include at least one valid source URL and no source older than six months.
- **SC-003**: Operators can retrieve the correct stored history record for user ID, session ID, and generation ID queries in 100% of scripted acceptance scenarios.
- **SC-004**: Governance reviewers can trace 100% of sampled accepted outputs to a generation identifier, user context, session context, source references, and related audit events.
- **SC-005**: Documentation validation for the generation path, retrieval path, and persistence path is completed before implementation sign-off with no unresolved compatibility gaps.

## Assumptions

- The target users are internal organizational users with Entra accounts and approved access to the CommercialScripting application.
- The Entra application registration supports an HTTPS redirect URI on the application domain for the browser callback path, such as `/auth/callback`.
- The allowlisted news corpus already exists or will be provisioned separately and can be ingested on a fixed cadence with canonical source URLs plus publication-date metadata needed for filtering.
- Mobile-specific optimization is out of scope for the first governed workflow release as long as the HTML5 experience remains usable in a desktop browser.
- Existing shared generation identity and audit contracts are available to this project and can be used without redefining downstream consumers.
- The direct Azure OpenAI SDK path is feasible on the approved Python runtime, and a direct REST path remains available if documentation validation exposes an SDK-specific limitation.
- If new persistence objects are required, they will be limited to append-only tables in a dedicated schema plus read-only views without changing existing database tables.

## Documentation Validation Update

- 2026-03-31: Validation matrix review confirmed the selected Entra PKCE flow, direct Azure OpenAI SDK path, scheduled Azure AI Search ingestion strategy, and append-only SQL boundary remain valid. No scope-changing refinements were required.
