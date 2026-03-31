# Implementation Plan: Governed Script Workflow

**Branch**: `001-governed-script-workflow` | **Date**: 2026-03-31 | **Spec**: `/home/shiwei/AIGovernDemoCode/AIGovernCommercialScripting/specs/001-governed-script-workflow/spec.md`
**Input**: Feature specification from `/home/shiwei/AIGovernDemoCode/AIGovernCommercialScripting/specs/001-governed-script-workflow/spec.md`

## Summary

Deliver a governed CommercialScripting web application that requires Entra sign-in, accepts script-generation prompts, grounds eligible responses with recent allowlisted news, persists generation and audit evidence in Azure SQL without changing existing tables, and exposes searchable history plus traceable governance contracts for downstream consumers. The implementation uses a static HTML5 frontend with MSAL.js, a stateless FastAPI backend on Python 3.12.3, direct Azure OpenAI SDK calls with a documented REST fallback, Azure AI Search for retrieval and scheduled ingestion, and dedicated append-only SQL objects plus read-only views for retrieval.

## Technical Context

**Language/Version**: Python 3.12.3 for the backend; HTML5, CSS, and ES2022 JavaScript for the frontend  
**Primary Dependencies**: FastAPI, Pydantic v2, openai, azure-identity, azure-search-documents, mssql-python, MSAL.js, pytest, httpx, Playwright for Python  
**Storage**: Azure SQL database `aigovernadvworksdb` using a dedicated append-only schema and read-only views; Azure AI Search index for allowlisted news retrieval  
**Testing**: pytest, pytest-asyncio, httpx, Playwright for Python, JSON Schema validation, OpenAPI contract validation  
**Target Platform**: Linux-hosted `CommercialScriptingVM` serving HTTPS traffic for an internal demo domain  
**Project Type**: Web application with static frontend, stateless Python web service, SQL persistence, and ARM deployment artifacts  
**Performance Goals**: History and audit search responses under 3 seconds p95 for demo-scale datasets; generation requests return a completed response or controlled failure within 30 seconds p95 under acceptance-test load; scheduled ingestion completes a normal delta refresh within 15 minutes  
**Constraints**: Entra-only access, no embedded credentials, no changes to existing SQL tables, allowlisted six-month news freshness, ARM JSON as the deployment artifact baseline, manual certificate or DNS steps documented explicitly, real evidence only  
**Scale/Scope**: Internal demo application for tens of concurrent users, one VM-hosted environment, one governed workflow, one allowlisted news corpus, and downstream consumers that rely on stable generation and audit contracts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- PASS: Entra authentication remains the only allowed access path. The frontend uses a dedicated CommercialScripting app registration with authorization code plus PKCE through MSAL.js and an HTTPS redirect path such as `/auth/callback`.
- PASS: The architecture remains an HTML5 frontend plus stateless Python backend over HTTPS. Secrets are supplied through environment variables and managed identity-capable connection settings rather than source-controlled secrets.
- PASS: Azure OpenAI orchestration is documentation-backed through the direct `openai` Python SDK with Azure Identity token support, Azure AI Search retrieval remains allowlisted and source-linked, and ingestion design enforces the six-month freshness rule.
- PASS: Shared generation identity and audit contracts are preserved through explicit response schemas and dedicated SQL objects. Existing tables in `aigovernadvworksdb` remain untouched.
- PASS: Acceptance coverage is planned for sign-in, grounded generation, history persistence, search by user ID, session ID, and generation ID, audit traceability, and ARM JSON deployment with documented certificate and DNS exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/001-governed-script-workflow/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── openapi.yaml
│   ├── generation-record.schema.json
│   └── audit-record.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   ├── config/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   └── main.py
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── requirements/

frontend/
├── src/
│   ├── auth/
│   ├── pages/
│   ├── services/
│   ├── styles/
│   └── app.js
├── public/
└── tests/

infra/
└── arm/

sql/
├── migrations/
└── views/

docs/
└── validation/
```

**Structure Decision**: Use a split web-application layout with `frontend/` for static HTML5 assets and browser-side auth, `backend/` for the stateless FastAPI service, `sql/` for new schema objects and read-only views, and `infra/arm/` for deployable ARM JSON artifacts. This keeps user-facing code, backend services, persistence objects, and deployment materials independently testable while matching the project boundary described in the constitution.

## Complexity Tracking

No constitution violations or justified complexity exceptions are required for this plan.

## Phase 0 Research Summary

- Research findings are documented in `/home/shiwei/AIGovernDemoCode/AIGovernCommercialScripting/specs/001-governed-script-workflow/research.md`.
- The selected stack favors Microsoft-documented authentication, Azure OpenAI, Azure AI Search, and Azure SQL patterns over framework-heavy alternatives.
- The plan treats LangChain as out of scope for implementation unless a later amendment reopens that decision.

## Phase 1 Design Summary

- The data model is documented in `/home/shiwei/AIGovernDemoCode/AIGovernCommercialScripting/specs/001-governed-script-workflow/data-model.md`.
- External interfaces are defined in `/home/shiwei/AIGovernDemoCode/AIGovernCommercialScripting/specs/001-governed-script-workflow/contracts/openapi.yaml` and the shared record schemas in the same directory.
- Delivery and bootstrap steps, environment variables, and manual deployment exceptions are documented in `/home/shiwei/AIGovernDemoCode/AIGovernCommercialScripting/specs/001-governed-script-workflow/quickstart.md`.

## Post-Design Constitution Check

- PASS: The design keeps user authentication in the browser with Entra PKCE and sends only authenticated API calls to the backend.
- PASS: The backend remains stateless. Session identity is carried as request metadata and persisted with generation and audit records rather than stored as server-side login state.
- PASS: Generation identity, source references, and audit records have explicit contract schemas and append-only persistence objects that do not modify existing tables.
- PASS: Retrieval design uses a scheduled allowlisted ingestion process with canonical URLs and publication timestamps normalized before indexing.
- PASS: Quickstart and contract artifacts include the required validation checkpoints, environment variables, ARM JSON deployment expectations, and manual certificate or consent steps.

## Documentation Validation Update

- 2026-03-31: Service compatibility validation completed with no architecture-breaking findings. Planned implementation tracks remain unchanged.
