.PHONY: install install-frontend format format-check lint typecheck test frontend-check check

install:
	python3 -m pip install -e ".[dev]"

install-frontend:
	npm --prefix frontend ci

format:
	python3 -m ruff format backend

format-check:
	python3 -m ruff format --check backend

lint:
	python3 -m ruff check backend

typecheck:
	python3 -m mypy backend

test:
	python3 -m pytest

frontend-check:
	npm --prefix frontend run build

check: format-check lint typecheck test frontend-check
