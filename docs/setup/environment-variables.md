# Environment Variables

The runtime reads configuration strictly from environment variables.

- ENTRA_TENANT_ID: Tenant ID for Entra authentication.
- ENTRA_CLIENT_ID: SPA client ID used by frontend and backend claim validation.
- ENTRA_AUTHORITY: Entra authority URL.
- ENTRA_REDIRECT_URI: HTTPS callback URI used by MSAL PKCE.
- APP_BASE_URL: Public HTTPS origin for the hosted app.
- API_BASE_URL: HTTPS backend API base URL.
- AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint.
- AZURE_OPENAI_DEPLOYMENT: Deployment/model name.
- AZURE_OPENAI_API_VERSION: Pinned Azure OpenAI API version.
- AZURE_OPENAI_API_KEY: Azure OpenAI API key used by backend generation calls.
- AI_SEARCH_ENDPOINT: Azure AI Search endpoint.
- AI_SEARCH_INDEX_NAME: Index that stores allowlisted news.
- AI_SEARCH_ALLOWLIST_PATH: Runtime path for approved source allowlist.
- AI_SEARCH_API_KEY: Azure AI Search API key used by backend retrieval calls.
- AZURE_SQL_CONNECTIONSTRING: Entra-capable SQL connection string.
- GOVERNANCE_SQL_SCHEMA: Schema for new append-only objects.
- TLS_CERT_PATH: Certificate path for HTTPS serving.
- TLS_KEY_PATH: Key path for HTTPS serving.
- AUDIT_CONTRACT_VERSION: Contract version label for persisted evidence.

How to obtain the API keys:

- AZURE_OPENAI_API_KEY: Azure Portal -> Azure OpenAI resource -> Keys and Endpoint -> KEY 1 or KEY 2.
- AI_SEARCH_API_KEY: Azure Portal -> Azure AI Search resource -> Keys -> Primary admin key (or a query key if permission scope is sufficient).

Secrets must not be committed. Store keys in environment-specific secret stores (for example, App Service settings or Key Vault references).
