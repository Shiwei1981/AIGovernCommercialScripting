# Phase 0 Research: Governed Script Workflow

## Decision: Use a static HTML5 frontend with MSAL.js for browser auth

- **Decision**: Implement the user-facing experience as static HTML5, CSS, and ES2022 JavaScript served from the application host, using `@azure/msal-browser` for Entra authorization code with PKCE.
- **Rationale**: The feature explicitly calls for an HTML5 frontend, and the Entra SPA guidance documents MSAL.js as the standard library for browser-based sign-in and token acquisition. A static frontend keeps the VM-hosted deployment simple and preserves the stateless backend requirement.
- **Alternatives considered**: A React or Vite application was rejected because it adds build and dependency overhead without a product requirement for a richer client framework. A backend-managed login flow was rejected because it would introduce server-side session state and a more complex cookie model.

## Decision: Use FastAPI as the stateless Python backend framework

- **Decision**: Use FastAPI with Pydantic v2 for the HTTPS backend API.
- **Rationale**: FastAPI provides explicit request and response models, generated OpenAPI output, and straightforward async integration for Azure service clients. That fits the contract-heavy governance requirement and simplifies test and documentation generation.
- **Alternatives considered**: Flask was rejected because it would require more manual schema and validation work for the same contract surface. Django was rejected because it introduces stateful and ORM-oriented defaults that are unnecessary for a small stateless service.

## Decision: Use the direct Azure OpenAI Python SDK with Azure Identity

- **Decision**: Use the `openai` Python package against the Azure OpenAI endpoint with `azure-identity` token acquisition as the primary generation path. Keep a direct REST implementation path documented as the fallback.
- **Rationale**: The current Azure documentation shows the direct Python SDK pattern and Azure Identity token provider flow. This keeps the generation path closest to the authoritative service surface and reduces abstraction risk compared with LangChain.
- **Alternatives considered**: LangChain was rejected for the initial implementation because the clarified spec now treats it as out of scope unless re-approved. A REST-first implementation was rejected as primary because the SDK gives a cleaner typed surface while preserving a direct fallback path.

## Decision: Use scheduled allowlisted ingestion into Azure AI Search

- **Decision**: Populate the news corpus through a scheduled ingestion process that admits only allowlisted articles, normalizes canonical URLs and UTC publication timestamps, and upserts documents into a dedicated Azure AI Search index.
- **Rationale**: The Azure AI Search indexing APIs support explicit upload and merge-or-upload workflows and make it possible to enforce required fields before content becomes queryable. Freshness guarantees are more defensible when publication date and canonical URL are normalized at ingestion time instead of inferred during retrieval.
- **Alternatives considered**: Query-time filtering over a broader unmanaged index was rejected because it cannot guarantee source completeness. Manual-only refresh was rejected as the primary path because it weakens freshness guarantees and creates an operational bottleneck.

## Decision: Persist history and audit evidence in a dedicated append-only SQL schema

- **Decision**: Create new append-only tables for generation records, source references, and audit events in a dedicated schema inside `aigovernadvworksdb`, plus read-only views for search and downstream consumption.
- **Rationale**: This satisfies the constitution's immutability rule for existing tables while keeping generation identity and audit evidence queryable in one authoritative store. Append-only writes preserve traceability and reduce the risk of accidental evidence mutation.
- **Alternatives considered**: Reusing or extending existing tables was rejected because the constitution forbids it. Storing evidence only in files or blobs was rejected because search by user, session, and generation ID requires structured query support.

## Decision: Use the `mssql-python` driver with Entra-capable connection strings

- **Decision**: Use `mssql-python` for Azure SQL connectivity, with environment-provided connection strings that support `ActiveDirectoryDefault` locally and a managed-identity-capable mode in the hosted VM environment.
- **Rationale**: Current Azure SQL Python guidance documents `mssql-python` and Entra-based passwordless connection patterns for FastAPI-style services. This keeps database access aligned with secure runtime configuration and avoids embedding SQL credentials.
- **Alternatives considered**: Username/password SQL authentication was rejected because it conflicts with the secure configuration rule. A heavier ORM-first stack was rejected because the initial persistence workload is append-only and query-focused rather than relationally complex.

## Decision: Test with pytest, httpx, Playwright for Python, and schema validation

- **Decision**: Use `pytest` as the unified test runner, `httpx` for API integration tests, Playwright for Python for browser sign-in and request-submission flows, and JSON Schema plus OpenAPI validation for contracts.
- **Rationale**: The constitution mandates both user-journey and contract evidence. A Python-centered test stack keeps backend, contract, and end-to-end testing under one runner while still exercising the browser experience.
- **Alternatives considered**: Selenium was rejected because Playwright is more reliable for modern browser flows and easier to script for controlled sign-in journeys. Postman-only contract testing was rejected because it would not integrate as cleanly into a reproducible CI workflow.

## Decision: Deploy as VM-hosted static files plus a Python API with ARM JSON artifacts

- **Decision**: Plan for ARM JSON artifacts that provision or document VM-adjacent infrastructure, while calling out manual certificate install, DNS binding, and Entra consent or redirect-URI steps as explicit exceptions.
- **Rationale**: The constitution requires ARM JSON planning while acknowledging that the VM and certificate baseline may still require manual steps in a demo environment. Documenting those steps preserves deployment traceability without pretending they are fully automated.
- **Alternatives considered**: App Service or container-first deployment was rejected for this feature because the planning prompt explicitly targets `CommercialScriptingVM`. Fully manual deployment was rejected because ARM JSON remains the required artifact standard.

## Validation Outcome Snapshot

- 2026-03-31: Documentation validation confirmed all selected decisions remain compliant.
- No decision reversals were required for Entra auth flow, Azure OpenAI primary path, Azure AI Search ingestion model, or SQL persistence boundary.