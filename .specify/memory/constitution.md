<!--
Sync Impact Report
Version change: unversioned template -> 1.0.0
Modified principles:
- placeholder principle 1 -> I. Entra-Gated User Access
- placeholder principle 2 -> II. Stateless Backend and Secure Configuration
- placeholder principle 3 -> III. Shared Contracts and Immutable Existing Tables
- placeholder principle 4 -> IV. Grounded Six-Month News Retrieval
- placeholder principle 5 -> V. Verification Before Implementation
Added sections:
- Operational Constraints
- Delivery and Evidence
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ✅ .github/prompts/*.md reviewed; no changes required
Follow-up TODOs:
- None
-->

# CommercialScripting Child Constitution

## Core Principles

### I. Entra-Gated User Access
Every user-facing surface MUST require Microsoft Entra ID authentication, and the
CommercialScripting child project MUST own the app registration used to serve that
experience. Anonymous access, local credential stores, and alternative primary sign-in
flows are prohibited unless an amendment explicitly authorizes them. Rationale: this
project is the portfolio's user-facing governed application, so identity provenance must
be consistent and auditable from sign-in through evidence retrieval.

### II. Stateless Backend and Secure Configuration
The application boundary MUST remain an HTML5 frontend calling a stateless Python backend
over HTTPS. Secrets and connection details MUST come from OS environment variables,
managed identity, or an equivalently secure runtime configuration source; credentials
MUST NOT be embedded in source, deployment artifacts, or client-delivered code.
Deployment planning MUST target CommercialScriptingVM and the demo domain baseline while
documenting any manual certificate, DNS, or VM-binding steps. Rationale: stateless
runtime behavior, secure secret handling, and explicit deployment exceptions keep the
demo architecture reproducible without normalizing unsafe shortcuts.

### III. Shared Contracts and Immutable Existing Tables
The generation identity model and audit record schema are authoritative shared contracts
for downstream governance projects and MUST be preserved in every spec, plan, and task
set. Existing database tables in aigovernadvworksdb are immutable; features MUST adapt by
using approved new objects or application-layer composition rather than altering existing
tables. Any proposal that would change an existing table or weaken contract fields MUST be
blocked until the constitution is amended. Rationale: downstream governance correlation
depends on stable contracts, and database immutability is an explicit portfolio boundary.

### IV. Grounded Six-Month News Retrieval
All generation workflows that use external context MUST retrieve it from an allowlisted
internet-news corpus served through Azure AI Search, include source URLs in returned
evidence, and enforce a freshness window of no more than six months. Azure OpenAI may be
orchestrated through LangChain only when documentation validation confirms compatibility;
otherwise the design MUST document and adopt a direct Azure OpenAI SDK or REST fallback.
Ungrounded generation paths that omit source linkage or freshness enforcement are not
compliant. Rationale: CommercialScripting must produce traceable, recent evidence rather
than opaque or stale AI output.

### V. Verification Before Implementation
Every material change to requirements, contracts, deployment assumptions, or integration
choices MUST update the child specification, plan, checklist, and tasks before
implementation proceeds. Acceptance coverage MUST include sign-in, grounded generation,
history persistence, search by user ID, session ID, and generation ID, and audit
traceability. Documentation validation MUST confirm Azure OpenAI behavior, LangChain
compatibility when proposed, Azure AI Search retrieval guarantees, Entra flow design, and
Azure SQL access patterns before integration code is treated as final. Rationale:
CommercialScripting is a governance-producing system, so documentation-backed validation
is part of the implementation contract rather than optional project hygiene.

## Operational Constraints

CommercialScripting owns the user-facing AI application, generation history, audit
evidence, and the primary contracts consumed by downstream governance projects.

In scope:
- HTML5 frontend for governed script-generation workflows.
- Entra-authenticated access.
- Stateless Python backend over HTTPS.
- Azure OpenAI integration with a documented orchestration path.
- Azure AI Search over an allowlisted internet-news corpus with six-month freshness and
	source URLs.
- Azure SQL-backed generation history and audit persistence.
- Search by user ID, session ID, and generation ID.

Out of scope:
- Governance dashboards owned by other child projects.
- SOC operations scenarios.
- Production-grade high availability or large-scale performance engineering.
- Modifications to existing database tables.

Naming and artifact conventions:
- Workspace directory: AIGovernCommercialScripting.
- Repository target: AIGovenDemoCommercialScripting.
- Required prompt artifacts live under .github/prompts and include speckit.constitution,
	speckit.specify, speckit.clarify, speckit.plan, speckit.checklist, speckit.tasks,
	speckit.implement, speckit.analyze, and speckit.taskstoissues prompt files.

## Delivery and Evidence

Plans and implementation tasks MUST preserve the Step 2 governance rules while defining
the Step 3 application boundary in enough detail to execute safely.

Delivery expectations:
- Frontend and backend interactions MUST be documented as HTTPS calls from the HTML5
	client to the stateless Python service.
- Environment variables MUST be defined for tenant, client, endpoint, deployment, API
	version, AI Search, SQL, and certificate-related runtime settings.
- Native ARM JSON remains the required deployment artifact format; any manual certificate
	install, DNS binding, consent, or VM configuration step MUST be called out explicitly.
- Runtime endpoints MUST align with the demo domain and VM baseline without embedding
	credentials.

Evidence expectations:
- Generated outputs MUST retain source references and audit events sufficient for
	downstream cross-project correlation.
- History retrieval MUST support user ID, session ID, and generation ID without changing
	existing tables.
- Review artifacts MUST make real evidence traceable; fabricated evidence or placeholder
	audit paths are prohibited in accepted work.

## Governance

This constitution supersedes conflicting local prompts, templates, and implementation
habits for the CommercialScripting child project.

Amendment procedure:
- Amendments MUST be proposed by updating this file together with any affected templates,
	prompts, specs, plans, and task guidance.
- An amendment is not complete until its Sync Impact Report identifies every dependent
	artifact reviewed and marks pending follow-up explicitly.
- Changes that alter scope boundaries, security posture, contract authority, database
	immutability, or retrieval guarantees require approval before implementation resumes.

Versioning policy:
- MAJOR versions apply to backward-incompatible governance changes or removal of a core
	principle.
- MINOR versions apply to added principles, new mandatory sections, or materially expanded
	obligations.
- PATCH versions apply to clarifications that do not change required behavior.

Compliance review expectations:
- Every spec, plan, checklist, and task set MUST include an explicit constitution check.
- Reviews MUST block work that lacks Entra-gated access, secure configuration, contract
	preservation, compliant retrieval evidence, or the mandated validation coverage.
- Runtime and documentation decisions MUST be re-validated whenever Azure service behavior
	or deployment assumptions materially change.

**Version**: 1.0.0 | **Ratified**: 2026-03-31 | **Last Amended**: 2026-03-31
