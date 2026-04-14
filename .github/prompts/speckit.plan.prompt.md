---
agent: speckit.plan
---

# CommercialScripting Planning Prompt

## Planning Approach

Create an implementation-ready plan for the CommercialScripting child project that preserves Step 2 governance rules while defining the app boundary in enough detail for Step 3 execution.

## Required Plan Outputs

- Architecture decisions with rationale and rejected alternatives.
- Integration boundaries for Entra, Azure OpenAI, Azure AI Search, and Azure SQL.
- A phased delivery plan (MVP first, then incremental hardening).
- Risk register with mitigation and rollback strategy.
- Environment variable matrix for local test and Azure Web App runtime.

## Architecture Direction

- HTML5 client plus stateless Python backend.
- Entra-authenticated user journey.
- Azure OpenAI generation service using direct SDK with direct REST fallback.
- Azure AI Search retrieval pipeline over an allowlisted corpus.
- Azure SQL persistence for history and audit evidence.

## Service Interactions

- Frontend authenticates users and calls the backend over HTTPS.
- Backend calls Azure OpenAI and Azure AI Search using its own app registration and secure runtime configuration.
- Backend writes generation identity and audit records to Azure SQL.

## Deployment Model

- Build and package frontend and backend deliverables into one Docker image.
- Push versioned images to Azure Container Registry (ACR).
- Deploy containers to Azure Web App and manage release via image tags.
- Document custom domain, TLS certificate binding, or consent steps as explicit manual exceptions when needed.

## Testing Strategy

- UI authentication and request submission tests.
- API tests for generation, retrieval, and history search.
- Contract validation tests for generation identity and audit records.
- Include a developer-machine direct test workflow that runs frontend and backend without Docker packaging, ACR, or Azure Web App deployment.
- Documentation-validation tasks for Azure OpenAI, AI Search, Entra, and Azure SQL.

## Planning Requirements

- Define environment variables for tenant, client, endpoint, deployment, API version, AI Search, SQL, and runtime app settings injected by Azure Web App.
- Define repo bootstrap and push expectations for `AIGovenDemoCommercialScripting`.
- Preserve database immutability and real-evidence rules.
- Explicitly prohibit placeholder or stub implementations in the delivery plan.
- Require each integration workstream to define real implementation tasks and acceptance criteria, not mock-only behavior.
- Require an explicit local test runbook for development test machines that validates core workflows before container publishing.
- Require uncertain decisions to use defaults tagged "待 clarify 确认" with owner and follow-up date.
- Prohibit deriving normative constraints from deleted implementation history.
- Treat LangChain as out of scope unless a later governance amendment re-authorizes it.
- Require traceability from plan sections back to spec requirements and constraints.
