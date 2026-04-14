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
- Azure OpenAI through direct SDK with direct REST fallback.
- Azure AI Search over an allowlisted internet-news corpus with six-month freshness and source URLs.
- Azure SQL-backed generation history and audit persistence.
- Search by user ID, session ID, and generation ID.

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
- LangChain is out of scope and cannot be treated as an approved implementation path.
- Core business flows must be implemented as real runtime code; placeholder, hardcoded, or mock-only logic cannot be treated as complete delivery.
- Constraints cannot use deleted implementation history as mandatory basis.
- Uncertain decisions must use defaults tagged as "待 clarify 确认" until resolved.

## Security, Identity, and Deployment Principles

- CommercialScripting owns its own Entra app registration.
- The backend remains stateless unless an amendment explicitly approves otherwise.
- Deployment planning must package code as Docker images, publish to ACR, and deploy to Azure Web App.
- Frontend and backend deployment outputs must be combined into one Docker image/container.
- Runtime configuration must be injected through Azure Web App App Settings without embedding credentials.
- Runtime endpoints must align to the configured Azure Web App domain baseline while preserving VM-hosted HTML5 access assumptions.

## Testing and Change Control

- Every change to app requirements, contracts, or deployment assumptions must update the child spec, plan, checklist, and tasks before implementation proceeds.
- Acceptance tests must cover sign-in, grounded generation, history persistence, search, and audit traceability.
- A simplest-path local development-machine test method must be maintained to validate core workflows without Docker packaging, ACR push, or Azure Web App release.
- Documentation validation must confirm direct Azure OpenAI SDK/REST behavior, Azure AI Search retrieval, Entra flow, and Azure SQL access patterns.
- Requirements traceability from spec -> plan -> tasks -> implementation must be preserved for all governance-critical flows.

## Naming and Artifact Conventions

- Directory: `AIGovernCommercialScripting`
- Repository: `AIGovenDemoCommercialScripting`
- Required files: `speckit.constitution.prompt.md`, `speckit.specify.prompt.md`, `speckit.clarify.prompt.md`, `speckit.plan.prompt.md`, `speckit.checklist.prompt.md`, `speckit.tasks.prompt.md`, `speckit.implement.prompt.md`, `speckit.analyze.prompt.md`, `speckit.taskstoissues.prompt.md`
