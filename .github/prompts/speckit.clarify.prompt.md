---
agent: speckit.clarify
---

# CommercialScripting Clarification Prompt

## Highest-Value Questions

- Which Azure AI Search indexing and refresh mechanism will guarantee six-month freshness and source URLs for the allowlisted corpus?
- Does LangChain remain the approved orchestration layer after documentation validation, or should the project switch to direct Azure OpenAI SDK or REST usage?
- What exact Entra sign-in flow and redirect URI pattern best fit the VM-hosted HTML5 app?
- Which new SQL objects are allowed for history and audit persistence without touching existing tables?

## Assumptions If Unanswered

- Azure AI Search is retained with an explicit fallback to a smaller manually refreshed allowlist if automation is insufficient.
- LangChain stays provisional until validated.
- The app uses a single dedicated Entra app registration.
- VM-bound certificate trust steps will be documented as manual deployment exceptions.

## Blockers vs Non-Blockers

- Blocker: inability to define compliant generation identity and audit contracts.
- Blocker: unsupported authentication or Azure OpenAI integration path.
- Non-blocker: exact UI language wording.
- Non-blocker: whether scheduled refresh is timer-triggered or manually invoked, if the retrieval contract remains intact.

## Documentation-Validation Concerns

- Azure OpenAI preview API compatibility.
- Azure AI Search indexing, retrieval, and freshness guarantees.
- Entra ID auth flow for VM-hosted HTML5 apps.
- Azure SQL secure connection guidance.
