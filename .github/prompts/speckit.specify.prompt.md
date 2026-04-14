---
agent: speckit.specify
---

# CommercialScripting Child Specification Prompt

## Purpose

Produce the Step 3 feature specification for CommercialScripting as the governed AI application that emits the generation and audit evidence consumed by the other portfolio projects.

## Required Functional Requirements

- HTML5 frontend with Entra ID sign-in.
- Stateless Python backend and HTML5 frontend deployed together in a single Docker image on Azure Web App for Linux.
- Azure OpenAI generation path validated against official docs, with direct SDK as the primary integration path.
- LangChain is optional and can only be used if documentation validation confirms compatibility; otherwise document the direct SDK or REST path.
- Azure AI Search retrieval over an allowlisted internet-news corpus with article URLs and a six-month freshness rule.
- Generation history persistence in Azure SQL database `aigovernadvworksdb`.
- Search and retrieval by user ID, session ID, and generation ID.
- Audit event creation for user and generation actions.
- Runtime configuration must come from Azure Web App application settings (environment variables), not image-bundled secrets.

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
- Azure Web App app settings are missing, malformed, or inconsistent across deployment slots.
- Azure Web App default domain callback mismatch causes Entra sign-in failure.

## Non-Functional Requirements

- Entra authentication and least-privilege downstream access are mandatory.
- Runtime evidence must be real and traceable.
- Native ARM JSON remains the deployment artifact standard.
- Python 3.12.3 compatibility and HTML5 delivery patterns are the default.
- POC release path uses Azure Web App default domain and platform-managed TLS certificate.

## Required Azure and Microsoft Services

- Entra ID
- Azure OpenAI
- Azure AI Search
- Azure SQL
- Azure Web App for Linux (single-container host)

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
- Documentation-validation checkpoints for Azure OpenAI SDK/REST, optional LangChain compatibility, AI Search, Entra, and Azure SQL.
