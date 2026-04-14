---
agent: speckit.analyze
---

# CommercialScripting Cross-Artifact Analyze Prompt

Perform a non-destructive consistency and quality review across spec, plan, and tasks for the CommercialScripting project.

## Analyze Scope

- Verify consistency of deployment model: single Docker image -> ACR -> Azure Web App.
- Verify runtime configuration model: Azure Web App App Settings injection.
- Verify local developer-machine direct testing requirements are present and coherent.
- Verify no placeholder or mock-only implementation is treated as done.

## Required Output

- Findings ordered by severity (Critical, High, Medium, Low).
- Exact artifact references for each finding.
- Missing requirement list.
- Drift list (conflicting statements across files).
- Recommended minimal corrections.

If no issues are found, explicitly state that artifacts are consistent and identify residual risks.
