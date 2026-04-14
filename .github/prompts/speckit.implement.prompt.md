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
- Docker build, image tagging, and publish artifacts for ACR, with frontend and backend packaged into one image/container.
- Azure Web App deployment artifacts and runtime App Settings configuration.
- Test suites and supporting validation scripts.
- Local developer-machine direct testing scripts/instructions that validate core workflows without Docker packaging, ACR push, or Azure Web App release.

## Secrets and Identity

- Use OS environment variables, managed identity, or equivalent secure runtime configuration.
- Register a dedicated Entra app for the frontend and any separate backend resource access path if required by the final auth design.

## Validation Requirements

- Confirm Azure OpenAI and AI Search APIs against official docs before locking integration code.
- Confirm SQL auth and connection guidance before finalizing persistence code.
- Require passing tests for sign-in, grounded generation, history search, and audit traceability before completion.
- Do not deliver placeholder, stub, or mock-only code for core capabilities; implement real Entra, OpenAI, AI Search, and SQL runtime paths.
- Use direct Azure OpenAI SDK as mandatory integration path with documented direct REST fallback; do not adopt LangChain.
- Apply safe defaults for unresolved decisions and tag each as "待 clarify 确认" with owner and due date.
- Do not enforce constraints derived from deleted implementation history.

## Implementation Guardrails

- Prefer incremental modification on existing code over project regeneration.
- Avoid broad rewrites when targeted fixes satisfy the requirement.
- Keep contracts and public API behavior stable unless a spec/task explicitly requires a change.
