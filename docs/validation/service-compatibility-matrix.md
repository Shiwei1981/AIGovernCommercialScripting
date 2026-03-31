# Service Compatibility Matrix

This matrix tracks documentation validation outcomes that can force spec/plan refinements before implementation continues.

| Service Area | Validation Scope | Source Status | Decision | Action |
|---|---|---|---|---|
| Azure OpenAI | SDK support, API version pinning, fallback path | Validated against current SDK docs | Use direct SDK first, keep REST fallback | Keep `AZURE_OPENAI_API_VERSION` pinned and test both paths |
| LangChain | Compatibility with selected model and retrieval flow | Not required for current implementation | Deferred by design | No runtime dependency |
| Azure AI Search | Index schema, ingest upsert, freshness filtering | Validated for scheduled ingestion and query filters | Approved | Enforce canonical URL and six-month freshness at ingest + query |
| Entra ID | SPA PKCE sign-in and API token validation | Validated for authorization code + PKCE | Approved | Use MSAL browser flow and JWT claim checks in backend |
| Azure SQL | Entra-capable connectivity and append-only persistence | Validated for new schema and read-only views | Approved | Create `governance_history` objects only; do not modify existing tables |

## Refinement Trigger

If any row changes from Approved to Blocked, update the following before further implementation:

- `specs/001-governed-script-workflow/spec.md`
- `specs/001-governed-script-workflow/plan.md`
- `specs/001-governed-script-workflow/research.md`
