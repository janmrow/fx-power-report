.PHONY: help install lint fmt test ci

help:
	@echo "Targets:"
	@echo "  install  - install package in editable mode with dev dependencies"
	@echo "  lint     - run ruff checks"
	@echo "  fmt      - format code with ruff"
	@echo "  test     - run pytest"
	@echo "  ci       - run lint + test"

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

lint:
	ruff check .

fmt:
	ruff format .

test:
	pytest -q

ci: lint test
