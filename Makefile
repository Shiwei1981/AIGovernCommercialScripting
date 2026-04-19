PYTHON ?= python3

.PHONY: test test-unit test-contract test-integration lint

test:
	$(PYTHON) -m pytest tests/unit tests/contract tests/integration

test-unit:
	$(PYTHON) -m pytest tests/unit

test-contract:
	$(PYTHON) -m pytest tests/contract

test-integration:
	$(PYTHON) -m pytest tests/integration

lint:
	$(PYTHON) -m ruff check app tests
