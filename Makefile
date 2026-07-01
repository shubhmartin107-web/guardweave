.PHONY: install dev test lint clean run-api run-dashboard docker-build docker-up

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/

clean:
	rm -rf *.egg-info build dist
	rm -rf .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

run-api:
	uvicorn guardweave.api.server:create_app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	guardweave agent dashboard

docker-build:
	docker build -t guardweave .

docker-up:
	docker compose up

init-db:
	guardweave init

apply-default-policy:
	guardweave policy apply policies/default.yaml
