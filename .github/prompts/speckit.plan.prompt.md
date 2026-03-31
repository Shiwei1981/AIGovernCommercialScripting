---
agent: speckit.plan
---

# CommercialScripting Planning Prompt

## Planning Approach

Create an implementation-ready plan for the CommercialScripting child project that preserves Step 2 governance rules while defining the app boundary in enough detail for Step 3 execution.

## Architecture Direction

- HTML5 client plus stateless Python backend.
- Entra-authenticated user journey.
- Azure OpenAI generation service with documented orchestration choice.
- Azure AI Search retrieval pipeline over an allowlisted corpus.
- Azure SQL persistence for history and audit evidence.

## Service Interactions

- Frontend authenticates users and calls the backend over HTTPS.
- Backend calls Azure OpenAI and Azure AI Search using its own app registration and secure runtime configuration.
- Backend writes generation identity and audit records to Azure SQL.

## Deployment Model

- Target `CommercialScriptingVM`.
- Use native ARM JSON planning for deployable artifacts.
- Document certificate install, DNS binding, or consent steps as explicit manual exceptions.

## Testing Strategy

- UI authentication and request submission tests.
- API tests for generation, retrieval, and history search.
- Contract validation tests for generation identity and audit records.
- Documentation-validation tasks for Azure OpenAI, AI Search, Entra, and Azure SQL.

## Planning Requirements

- Define environment variables for tenant, client, endpoint, deployment, API version, AI Search, SQL, and certificate paths.
- Define repo bootstrap and push expectations for `AIGovenDemoCommercialScripting`.
- Preserve database immutability and real-evidence rules.
