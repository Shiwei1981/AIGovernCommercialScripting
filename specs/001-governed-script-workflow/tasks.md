# Tasks: Governed Script Workflow

**Input**: Design documents from `/specs/001-governed-script-workflow/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED by the feature specification and constitution. This plan includes sign-in, generation, retrieval/search, audit traceability, failure handling, and documentation-validation coverage.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize repository structure, tooling, and delivery scaffolding.

 - [X] T001 Create project directories in frontend/, backend/, infra/arm/, sql/, and docs/validation/
 - [X] T002 Initialize backend dependency manifests in backend/requirements/base.txt and backend/requirements/dev.txt
 - [X] T003 [P] Initialize frontend package and scripts in frontend/package.json
 - [X] T004 [P] Add CI workflow for lint and test execution in .github/workflows/ci.yml
 - [X] T005 [P] Create runtime configuration template in .env.example and docs/setup/environment-variables.md
 - [X] T006 Add repository bootstrap and push guide for AIGovenDemoCommercialScripting in docs/setup/repository-bootstrap.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core foundations that must be complete before user story implementation.

**CRITICAL**: No user story task starts before this phase is complete.

 - [X] T007 Build documentation-validation matrix for Azure OpenAI, LangChain decision gate, AI Search, Entra, and Azure SQL in docs/validation/service-compatibility-matrix.md
 - [X] T008 Update design docs when validation findings require refinements in specs/001-governed-script-workflow/spec.md, specs/001-governed-script-workflow/plan.md, and specs/001-governed-script-workflow/research.md
 - [X] T009 Define Entra app registration and redirect configuration steps in docs/entra/app-registration.md
 - [X] T010 Implement backend environment settings loader in backend/src/config/settings.py
 - [X] T011 [P] Implement JWT validation dependency for Entra tokens in backend/src/api/dependencies/auth.py
 - [X] T012 [P] Scaffold FastAPI app, middleware wiring, and route registration in backend/src/main.py
 - [X] T013 [P] Implement request correlation and structured logging middleware in backend/src/api/middleware/request_context.py
 - [X] T014 Create append-only governance schema migration baseline in sql/migrations/001_create_governance_schema.sql
 - [X] T015 [P] Create shared backend contract models aligned to JSON schemas in backend/src/models/contracts.py
 - [X] T016 [P] Scaffold frontend authentication shell and route guards in frontend/src/app.js

**Checkpoint**: Foundation complete, user stories can proceed.

---

## Phase 3: User Story 1 - Submit a Governed Generation Request (Priority: P1) 🎯 MVP

**Goal**: Authenticated user signs in and submits a generation request with compliant, source-linked recent-news grounding.

**Independent Test**: Sign in with Entra, submit prompt, receive governed output with valid citations or controlled failure with traceability.

### Tests for User Story 1

 - [X] T017 [P] [US1] Add browser sign-in and submit journey test in frontend/tests/e2e/test_signin_and_generate.py
 - [X] T018 [P] [US1] Add generation success and controlled-failure integration tests in backend/tests/integration/test_generation_flow.py
 - [X] T019 [P] [US1] Add POST /api/generations contract test in backend/tests/contract/test_generations_create_contract.py

### Implementation for User Story 1

 - [X] T020 [P] [US1] Implement MSAL PKCE client configuration in frontend/src/auth/msalConfig.js
 - [X] T021 [US1] Implement frontend sign-in, token acquisition, and sign-out flow in frontend/src/auth/authClient.js
 - [X] T022 [P] [US1] Implement allowlisted retrieval query service against Azure AI Search in backend/src/services/search_retrieval_service.py
 - [X] T023 [P] [US1] Implement Azure OpenAI SDK client with REST fallback client in backend/src/services/openai_generation_service.py
 - [X] T024 [US1] Implement scheduled allowlist ingestion and index upsert job in backend/src/services/news_ingestion_job.py
 - [X] T025 [US1] Implement governed generation orchestration service in backend/src/services/governed_generation_service.py
 - [X] T026 [US1] Implement generation and source-reference persistence repository in backend/src/repositories/generation_repository.py
 - [X] T027 [US1] Implement audit-event persistence repository for generation events in backend/src/repositories/audit_repository.py
 - [X] T028 [US1] Implement POST generation endpoint and controlled failure mapping in backend/src/api/routes/generations.py
 - [X] T029 [US1] Implement frontend generation form and citation rendering flow in frontend/src/pages/generate.js

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Retrieve Generation History (Priority: P2)

**Goal**: Operator retrieves stored generation history by user ID, session ID, or generation ID.

**Independent Test**: Seed records and verify each query key returns the correct generation history set without modifying existing tables.

### Tests for User Story 2

 - [X] T030 [P] [US2] Add history search contract test for GET /api/generations in backend/tests/contract/test_generations_search_contract.py
 - [X] T031 [P] [US2] Add history search integration tests for user/session/generation filters in backend/tests/integration/test_generation_history_search.py
 - [X] T032 [P] [US2] Add frontend history retrieval journey test in frontend/tests/e2e/test_history_search.py

### Implementation for User Story 2

 - [X] T033 [P] [US2] Create append-only generation and audit tables migration in sql/migrations/002_create_governance_history_tables.sql
 - [X] T034 [P] [US2] Create read-only history and audit projection views in sql/views/001_governance_history_views.sql
 - [X] T035 [US2] Implement history query repository for user/session/generation filters in backend/src/repositories/history_repository.py
 - [X] T036 [US2] Implement query validator for supported identifiers and input normalization in backend/src/services/history_query_validator.py
 - [X] T037 [US2] Implement GET /api/generations history search endpoint in backend/src/api/routes/generation_history.py
 - [X] T038 [US2] Implement GET /api/generations/{generationId} detail endpoint in backend/src/api/routes/generation_details.py
 - [X] T039 [US2] Implement frontend history search UI by user/session/generation ID in frontend/src/pages/history.js

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Trace Governance Evidence (Priority: P3)

**Goal**: Governance reviewer traces a generation to identity, source references, and audit events for downstream correlation.

**Independent Test**: Retrieve one generation audit trace and verify identifiers, citations, and audit events are complete for cross-project linkage.

### Tests for User Story 3

 - [X] T040 [P] [US3] Add GET /api/generations/{generationId}/audit contract test in backend/tests/contract/test_generation_audit_contract.py
 - [X] T041 [P] [US3] Add end-to-end audit trace integration test in backend/tests/integration/test_audit_trace_retrieval.py
 - [X] T042 [P] [US3] Add shared schema compatibility tests for generation and audit records in backend/tests/contract/test_shared_schema_compatibility.py

### Implementation for User Story 3

 - [X] T043 [P] [US3] Implement audit trace projection repository in backend/src/repositories/audit_trace_repository.py
 - [X] T044 [US3] Implement sign-in, history-search, and audit-view event emitter service in backend/src/services/audit_event_service.py
 - [X] T045 [US3] Implement GET /api/generations/{generationId}/audit endpoint in backend/src/api/routes/audit_trace.py
 - [X] T046 [US3] Implement reviewer audit trace page in frontend/src/pages/audit-trace.js

**Checkpoint**: All user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, deployment, and evidence capture across stories.

 - [X] T047 [P] Add ARM deployment template for VM app, API settings, Search, and SQL references in infra/arm/commercialscripting.main.json
 - [X] T048 [P] Document VM certificate install, DNS binding, and Entra consent manual exceptions in docs/deployment/vm-manual-binding-steps.md
 - [X] T049 [P] Add deployment parameters and environment mapping in infra/arm/commercialscripting.parameters.json
 - [X] T050 Run full acceptance suite for sign-in, generation, search, audit, and failure handling in backend/tests/integration/test_acceptance_suite.py
 - [X] T051 Produce validation evidence log with Azure service documentation checks in docs/validation/azure-documentation-validation.md
 - [X] T052 Finalize traceability updates in specs/001-governed-script-workflow/quickstart.md and specs/001-governed-script-workflow/checklists/governance.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) has no dependencies and starts immediately.
- Foundational (Phase 2) depends on Setup completion and blocks all user stories.
- User Story phases (Phase 3-5) depend on Foundational completion.
- Polish (Phase 6) depends on completion of all targeted user stories.

### User Story Dependencies

- US1 (P1) depends only on Foundational phase.
- US2 (P2) depends on Foundational phase and integrates persistence from US1 outputs, while remaining independently testable.
- US3 (P3) depends on Foundational phase plus persisted generation/history data from US1 and US2.

### Dependency Graph

- US1 -> US2 -> US3 for delivery order and incremental value.
- US2 and US3 can begin in parallel after Foundational if test fixtures are available, but priority execution remains P1 first.

### Within Each User Story

- Write tests first and confirm they fail for the intended behavior.
- Implement models/repositories before service orchestration.
- Implement service orchestration before endpoints and frontend wiring.
- Complete story acceptance validation before moving to the next priority story.

## Parallel Execution Examples

### User Story 1

- Run T017, T018, and T019 in parallel as separate test files.
- Run T022 and T023 in parallel as independent backend service modules.

### User Story 2

- Run T030, T031, and T032 in parallel as independent test suites.
- Run T033 and T034 in parallel as SQL files in separate migration/view paths.

### User Story 3

- Run T040, T041, and T042 in parallel as separate contract and integration tests.
- Run T043 and T044 in parallel as repository and service modules.

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1) end-to-end.
3. Validate sign-in, governed generation, controlled failure handling, and audit persistence.
4. Demo MVP before adding retrieval and reviewer trace experiences.

### Incremental Delivery

1. Add US1 for governed generation.
2. Add US2 for searchable history retrieval.
3. Add US3 for governance traceability and downstream evidence quality.
4. Complete Polish for ARM deployment artifacts and validation evidence.

### Parallel Team Strategy

1. Team aligns on Setup and Foundational tasks first.
2. After Foundational completion, assign story leads by phase while preserving dependency order.
3. Keep contract tests and schema validation owned centrally to prevent cross-story drift.

## Notes

- [P] tasks are safe to parallelize because they target separate files without incomplete dependencies.
- Story labels map each task to one user story for independent implementation and validation.
- Existing database tables remain immutable; persistence tasks are limited to new append-only schema objects and read-only views.
- Any documentation-validation finding that changes behavior must be reflected in spec and plan updates before implementation proceeds.
