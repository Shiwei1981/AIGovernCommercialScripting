---
agent: speckit.tasks
---
# CommercialScripting Task Prompt

Generate dependency-ordered Step 3 tasks for `AIGovenDemoCommercialScripting`.

## Task Quality Rules

- Tasks must be atomic and independently reviewable.
- Each task must reference impacted files or folders.
- Each task must include explicit acceptance criteria.
- Keep task size practical (target around 1-3 hours per task where possible).
- Reflect real dependency order and identify parallel-safe tasks.

## Must Include

- Spec and plan refinement tasks if documentation validation changes the design.
- Entra app registration and auth configuration tasks.
- HTML5 frontend tasks.
- Stateless Python backend tasks.
- Azure OpenAI integration tasks.
- Azure AI Search corpus and retrieval tasks.
- Azure SQL schema, persistence, and query tasks using only new objects when needed.
- Test tasks for sign-in, generation, search, audit, and error handling.
- Docker image build and versioning tasks.
- Tasks that ensure frontend and backend are packaged into one Docker image/container.
- ACR push and image publishing tasks.
- Azure Web App deployment and slot/release tasks.
- Azure Web App environment-variable injection (App Settings) tasks for runtime configuration.
- Tasks that define and validate a local developer-machine direct testing method without Docker packaging, ACR push, or Azure Web App release.
- Repo bootstrap and GitHub preparation tasks.
- Tasks that remove placeholder, stub, or mock-only logic and replace it with production-real code paths.
- Tasks that track each "待 clarify 确认" item to closure with explicit owner and artifact updates.
- Tasks that avoid deriving mandatory constraints from deleted implementation history.
- Tasks that implement direct Azure OpenAI SDK with direct REST fallback, without LangChain.
