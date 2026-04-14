---
agent: speckit.constitution
---

# CommercialScripting Child Constitution

## Purpose

Define the governing rules for the CommercialScripting child project, which owns the user-facing AI application, generation history, audit evidence, and the primary contracts consumed by downstream governance projects.

## Scope

- HTML5 frontend for governed script-generation workflows.
- Entra-authenticated access.
- Stateless Python backend over HTTPS.
- Azure OpenAI via direct Azure OpenAI SDK as primary path, with documented REST fallback.
- Azure AI Search over an allowlisted internet-news corpus with six-month freshness and source URLs.
- Azure SQL-backed generation history and audit persistence.
- Search by user ID, session ID, and generation ID.
- Single-container deployment model that hosts frontend and backend together.

## Non-Scope

- Governance dashboards owned by other child projects.
- SOC operations scenarios.
- Production-grade HA or large-scale performance engineering.
- Changes to existing database tables.

## Non-Negotiable Rules

- Entra ID authentication is mandatory for all user-facing surfaces.
- Secrets must come from OS environment variables, managed identity, or equivalent secure runtime configuration.
- Existing database tables are immutable.
- The generation identity model and audit record schema are authoritative shared contracts.
- News retrieval must remain allowlisted, source-linked, and limited to the last six months.

## Security, Identity, and Deployment Principles

- CommercialScripting owns its own Entra app registration.
- The backend remains stateless unless an amendment explicitly approves otherwise.
- Deployment planning must target Azure Web App for Linux containers and include container image rollout steps.
- Runtime endpoints must align to the Azure Web App default domain and platform-managed TLS certificate for POC releases.
- Secrets must be supplied through Azure Web App application settings (runtime environment variables), not embedded in images.

## Testing and Change Control

- Every change to app requirements, contracts, or deployment assumptions must update the child spec, plan, checklist, and tasks before implementation proceeds.
- Acceptance tests must cover sign-in, grounded generation, history persistence, search, and audit traceability.
- Documentation validation must confirm Azure OpenAI SDK/REST usage, Azure AI Search retrieval, Entra auth flow, and Azure SQL access patterns.

## Naming and Artifact Conventions

- Directory: `AIGovernCommercialScripting`
- Repository: `AIGovenDemoCommercialScripting`
- Required files: `speckit.constitution.md`, `speckit.specify.md`, `speckit.clarify.md`, `speckit.plan.md`, `speckit.checklist.md`, `speckit.tasks.md`, `speckit.implement.md`
