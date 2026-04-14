---
agent: speckit.specify
---

# CommercialScripting Child Specification Prompt

## Purpose

Produce the Step 3 feature specification for CommercialScripting as the governed AI application that emits the generation and audit evidence consumed by the other portfolio projects.

## Spec Output Quality Bar

- The spec must be implementation-agnostic, testable, and traceable.
- Every requirement should use explicit IDs (for example FR-001 style) and avoid ambiguous wording.
- Acceptance scenarios must be independently verifiable and mapped to user stories.
- Include assumptions, constraints, and measurable success criteria.

## Required Functional Requirements

- HTML5 frontend with Entra ID sign-in.
- VM-hosted HTML5 frontend and stateless Python HTTPS backend delivered through the approved container pipeline.
- Azure OpenAI generation path validated against official docs using direct SDK plus direct REST fallback.
- LangChain is not adopted.
- Azure AI Search retrieval over an allowlisted internet-news corpus with article URLs and a six-month freshness rule.
- Generation history persistence in Azure SQL database `aigovernadvworksdb`.
- Search and retrieval by user ID, session ID, and generation ID.
- Audit event creation for user and generation actions.

## Prioritized User Stories

1. End user signs in and submits a generation request with recent-news context.
2. End user retrieves generation history by user, session, or generation identifier.
3. Governance reviewer traces a generated output to source references and audit events.

## Acceptance Scenarios

1. Given an authorized Entra user, when the user signs in and submits a valid request, then the system returns a governed response with source-linked news context when applicable.
2. Given a stored generation, when an operator searches by user ID, session ID, or generation ID, then the matching history and audit context can be retrieved without modifying existing tables.
3. Given a downstream governance consumer, when it reads CommercialScripting contracts, then generation identity and audit fields are sufficient for cross-project correlation.

## Edge Cases

- Azure AI Search cannot satisfy freshness or source-URL guarantees for a requested article.
- Azure OpenAI preview behavior differs from expected documentation.
- Search results return incomplete source references.
- Existing database tables would need modification for a planned feature.
- Web App custom domain, TLS binding, or ingress policy creates demo-only access constraints.

## Non-Functional Requirements

- Entra authentication and least-privilege downstream access are mandatory.
- Runtime evidence must be real and traceable.
- Placeholder, mock-only, or hardcoded demo logic is not acceptable in delivered implementation requirements.
- Requirements must state that external integrations (Entra, Azure OpenAI, Azure AI Search, Azure SQL) are implemented as real runtime code paths.
- Deployment must package the app as Docker images, publish to Azure Container Registry (ACR), and release to Azure Web App.
- Frontend and backend must be packaged into one Docker image/container for deployment.
- Application configuration must be injected at runtime via Azure Web App environment variables (App Settings), with no embedded credentials.
- Uncertain decisions must adopt defaults tagged "待 clarify 确认" and tracked to closure.
- Constraints must not be derived from deleted implementation history.
- Python 3.12.3 compatibility and HTML5 delivery patterns are the default.

## Required Azure and Microsoft Services

- Entra ID
- Azure OpenAI
- Azure AI Search
- Azure SQL
- Azure Container Registry (ACR)
- Azure Web App for Containers (HTTPS endpoint)

## Data Sources and Outputs

- Input sources: user prompts, allowlisted AI Search news corpus, Entra identity claims.
- Output artifacts: generation records, source references, audit records, search results, child-spec documentation.

## Database Boundaries

- Use database `aigovernadvworksdb`.
- Do not modify existing tables.
- New tables, views, schemas, or helper objects must be justified explicitly.

## Required Tests and Verifiable Outcomes

- Sign-in flow validation.
- Generation success and failure-path tests.
- History search tests by user, session, and generation ID.
- Audit-record completeness validation.
- Define a simplest-path developer-machine test method that runs the system directly without Docker packaging, ACR push, or Azure Web App release.
- Documentation-validation checkpoints for direct Azure OpenAI SDK/REST, AI Search, Entra, and Azure SQL.

## Traceability Expectations

- The generated spec must clearly map user stories -> functional requirements -> acceptance scenarios -> success criteria.
- Deployment and runtime constraints (single container packaging and Web App App Settings injection) must be captured as requirements, not implementation notes.
