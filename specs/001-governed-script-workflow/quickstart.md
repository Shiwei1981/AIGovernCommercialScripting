# Quickstart: Governed Script Workflow

## Purpose

This document defines the expected bootstrap flow for implementing and validating the CommercialScripting governed workflow in the `AIGovenDemoCommercialScripting` repository.

## Prerequisites

- Linux development environment with Python 3.12.3 available.
- Access to the target Entra tenant, Azure OpenAI resource, Azure AI Search service, Azure SQL database `aigovernadvworksdb`, and the `CommercialScriptingVM` environment.
- An allowlisted news-source inventory and a canonical-URL normalization rule set.
- Permissions to register or update the CommercialScripting Entra application and configure redirect URIs.

## Repository Bootstrap

1. Create or clone the `AIGovenDemoCommercialScripting` repository.
2. Work only on the active feature branch `001-governed-script-workflow` until the planned tasks are generated and approved.
3. Scaffold the planned repository structure: `frontend/`, `backend/`, `infra/arm/`, `sql/`, and `docs/validation/`.
4. Create a Python virtual environment at the repository root and install backend and test dependencies.
5. Keep runtime secrets out of source control. Check in only placeholder configuration files such as `.env.example` if implementation tasks add them later.
6. Push the feature branch only after the feature docs, contracts, and implementation scaffolding remain consistent with the spec and constitution.

## Environment Variables

The implementation is expected to define and document at least the following runtime settings:

- `ENTRA_TENANT_ID`: Entra directory identifier for the CommercialScripting tenant.
- `ENTRA_CLIENT_ID`: Client ID for the browser-facing CommercialScripting SPA app registration.
- `ENTRA_AUTHORITY`: Authority URL for the Entra tenant.
- `ENTRA_REDIRECT_URI`: HTTPS redirect URI for the SPA callback, such as `https://<demo-domain>/auth/callback`.
- `API_BASE_URL`: HTTPS base URL for the backend API.
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI resource endpoint.
- `AZURE_OPENAI_DEPLOYMENT`: Azure OpenAI deployment name used for governed generation.
- `AZURE_OPENAI_API_VERSION`: API version pinned for the direct SDK or REST fallback.
- `AI_SEARCH_ENDPOINT`: Azure AI Search service endpoint.
- `AI_SEARCH_INDEX_NAME`: News index name used for grounding queries.
- `AI_SEARCH_ALLOWLIST_PATH`: Runtime-readable path or configuration entry for the approved source allowlist.
- `AZURE_SQL_CONNECTIONSTRING`: Entra-capable Azure SQL connection string for `aigovernadvworksdb`.
- `GOVERNANCE_SQL_SCHEMA`: Dedicated append-only schema name, expected to be `governance_history`.
- `APP_BASE_URL`: Public HTTPS origin for the VM-hosted application.
- `TLS_CERT_PATH`: Filesystem path to the deployed TLS certificate.
- `TLS_KEY_PATH`: Filesystem path to the deployed TLS private key or key reference.
- `AUDIT_CONTRACT_VERSION`: Version label for the shared generation and audit contract set.

## Local Development Flow

1. Authenticate to Azure with an account that has access to the Entra tenant and development resources.
2. Export or load the required environment variables from a secure local store.
3. Start the backend API with the planned FastAPI entry point.
4. Serve the static frontend over HTTPS locally or through the backend static-file host so the Entra redirect URI remains valid for testing.
5. Run the automated test suites for unit, integration, contract, and browser-driven acceptance coverage.

## Acceptance Validation Flow

1. Validate sign-in: a user reaches the governed workflow only after successful Entra authentication.
2. Validate governed generation: a grounded request returns source-linked evidence, or a controlled no-grounding response when compliant sources are unavailable.
3. Validate persistence: completed and failed generations both create retrievable generation and audit evidence.
4. Validate retrieval: searches by user ID, session ID, and generation ID return the expected read-only view results.
5. Validate audit traceability: reviewers can trace a stored output to generation identity, source references, and audit events.

## Documentation-Validation Checkpoints

- Confirm the direct Azure OpenAI SDK call pattern, pinned API version, and REST fallback before locking the generation implementation.
- Confirm the MSAL.js SPA PKCE flow and redirect-URI registration details before locking frontend auth code.
- Confirm the Azure AI Search index schema, indexing action strategy, and refresh cadence before locking the ingestion pipeline.
- Confirm the Azure SQL connection mode, Entra authentication pattern, and required database roles before locking persistence code.

## Deployment Expectations

- ARM JSON artifacts remain the primary deployment deliverables for resource configuration and repeatable environment setup.
- The VM host, certificate install, DNS binding, and any Entra consent or redirect-URI registration steps must be documented as manual exceptions if they cannot be fully automated.
- Hosted runtime configuration must use environment variables, managed identity, or an equivalent secure runtime source. Credentials must not be embedded in files served to the browser.

## Evidence to Capture During Implementation

- Screenshots or logs of successful Entra sign-in.
- Test evidence for grounded and controlled-failure generation paths.
- Query evidence for retrieval by user ID, session ID, and generation ID.
- Audit evidence that correlates one generation to its trace events and source references.
- Validation notes for Azure OpenAI, Azure AI Search, Entra auth, and Azure SQL access patterns.

## Traceability Update

- 2026-03-31: Implementation scaffolding, contract tests, SQL migrations, and validation artifacts were added to match the workflow acceptance boundaries and governance checklist.