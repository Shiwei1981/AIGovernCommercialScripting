---
agent: speckit.implement
---

# CommercialScripting Implementation Prompt

## Step 3 Execution Goal

Implement the governed CommercialScripting application and its supporting contracts without violating the Step 2 portfolio constraints.

## Create

- HTML5 frontend files.
- Stateless Python backend files.
- Azure SQL persistence objects that do not modify existing tables.
- Native ARM JSON deployment artifacts for Azure Web App for Linux container rollout.
- Single-container packaging assets that host frontend and backend together.
- Test suites and supporting validation scripts.

## Secrets and Identity

- Use OS environment variables, managed identity, or equivalent secure runtime configuration.
- For POC container releases, inject runtime settings via Azure Web App application settings; do not bundle secrets in container images.
- Register a dedicated Entra app for the frontend and any separate backend resource access path if required by the final auth design.

## Validation Requirements

- Confirm Azure OpenAI and AI Search APIs against official docs before locking integration code.
- Confirm SQL auth and connection guidance before finalizing persistence code.
- Require passing tests for sign-in, grounded generation, history search, and audit traceability before completion.
