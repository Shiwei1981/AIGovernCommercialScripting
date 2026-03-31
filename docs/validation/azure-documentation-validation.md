# Azure Documentation Validation Evidence

## Azure OpenAI

- Direct SDK path selected as primary implementation.
- API version pinned via `AZURE_OPENAI_API_VERSION`.
- REST fallback retained for controlled resilience.

## LangChain

- Not selected for runtime path in this feature iteration.
- Decision documented and can be revisited only by spec amendment.

## Azure AI Search

- Scheduled ingestion model selected.
- Canonical URL and publication timestamp required before indexing.
- Six-month freshness enforced by ingest and retrieval filters.

## Entra ID

- Browser sign-in uses authorization code with PKCE via MSAL.
- Backend validates tenant and audience claims from bearer tokens.

## Azure SQL

- Only new append-only schema objects and read-only views are introduced.
- Existing database tables are not modified.
