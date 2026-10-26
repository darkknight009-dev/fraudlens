.PHONY: install install-sdk install-frontend format format-check lint typecheck test sdk-test synthetic-evaluate train-model db-retention webhook-dispatch event-process frontend-check db-migrate db-bootstrap check

install:
	python3 -m pip install -e ".[dev]"

install-sdk:
	python3 -m pip install -e sdk/python

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

sdk-test:
	PYTHONPATH=sdk/python python3 -m pytest sdk/python/tests

synthetic-evaluate:
	PYTHONPATH=backend:. python3 scripts/evaluate_detector.py

train-model:
	PYTHONPATH=backend:. python3 scripts/train_model.py

db-retention:
	python3 -m app.cli.retention

webhook-dispatch:
	python3 -m app.cli.webhooks

event-process:
	python3 -m app.cli.events

frontend-check:
	npm --prefix frontend run build

db-migrate:
	python3 -m alembic upgrade head

db-bootstrap:
	python3 -m app.cli.bootstrap --scope transactions:score

check: format-check lint typecheck test sdk-test frontend-check
