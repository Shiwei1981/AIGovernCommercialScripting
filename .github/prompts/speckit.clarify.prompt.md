---
agent: speckit.clarify
---

# CommercialScripting Clarification Prompt

## Highest-Value Questions

- Which Azure AI Search indexing and refresh mechanism will guarantee six-month freshness and source URLs for the allowlisted corpus?
- Does LangChain remain the approved orchestration layer after documentation validation, or should the project switch to direct Azure OpenAI SDK or REST usage?
- What exact Entra sign-in flow and redirect URI pattern best fit the Azure Web App-hosted HTML5 app?
- Which new SQL objects are allowed for history and audit persistence without touching existing tables?
- Which modules currently contain placeholder logic and must be replaced by real integration code in this delivery cycle?
- What is the agreed single-container runtime composition for frontend plus backend (process model, static asset serving, startup contract)?
- What is the minimum local developer-machine test scope that must pass before any container publish step?

## Assumptions If Unanswered

- Azure AI Search is retained with an explicit fallback to a smaller manually refreshed allowlist if automation is insufficient.
- LangChain stays provisional until validated.
- The app uses a single dedicated Entra app registration.
- Web App custom-domain and TLS binding steps will be documented as manual deployment exceptions when required.
- Placeholder or mock-only code is treated as incomplete and must be converted to real runtime implementation.
- Frontend assets are served by the backend runtime within one deployable container image.
- Local direct tests are mandatory pre-publish checks.

## Blockers vs Non-Blockers

- Blocker: inability to define compliant generation identity and audit contracts.
- Blocker: unsupported authentication or Azure OpenAI integration path.
- Non-blocker: exact UI language wording.
- Non-blocker: whether scheduled refresh is timer-triggered or manually invoked, if the retrieval contract remains intact.

## Documentation-Validation Concerns

- Azure OpenAI preview API compatibility.
- Azure AI Search indexing, retrieval, and freshness guarantees.
- Entra ID auth flow for Azure Web App-hosted HTML5 apps.
- Azure SQL secure connection guidance.
