# Repository Bootstrap and Push Guide

Repository: AIGovenDemoCommercialScripting

## Bootstrap

1. Clone the repository.
2. Create and activate a Python 3.12.3 virtual environment.
3. Install backend dependencies:
   - `pip install -r backend/requirements/dev.txt`
4. Ensure environment variables are populated from a secure source.
5. Run tests before each push:
   - `pytest backend/tests -q`

## Branch and Push Expectations

1. Work on feature branch `001-governed-script-workflow` until feature completion.
2. Keep commit scope aligned to tasks from `specs/001-governed-script-workflow/tasks.md`.
3. Push only after lint/test checks pass and contracts/spec links remain up to date.
