---
agent: speckit.taskstoissues
---

# CommercialScripting Tasks-to-Issues Prompt

Convert tasks.md into dependency-ordered GitHub issues for implementation tracking.

## Conversion Rules

- Preserve dependency order and story grouping.
- One issue should represent one independently reviewable deliverable.
- Include acceptance criteria and impacted paths in each issue body.
- Mark blocking dependencies explicitly.
- Keep deployment and runtime constraints explicit:
	- Single Docker image containing frontend and backend.
	- ACR publish and Azure Web App deploy flow.
	- Azure Web App App Settings runtime configuration.
	- Local developer-machine direct test before publish.
- Include a checklist item to confirm no placeholder/mock-only logic remains.

## Issue Template Expectations

- Title: concise action statement.
- Description: requirement context and expected behavior.
- Definition of done: testable acceptance criteria.
- Dependencies: issue numbers or task IDs.
- Risk notes: rollback or mitigation hints when relevant.
