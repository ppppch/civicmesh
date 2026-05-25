SHELL := /bin/zsh

.PHONY: up down logs api web worker lint fmt

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

api:
	cd apps/api && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

worker:
	cd apps/worker-sim && uv run python -m src.supervisor

migrate:
	./scripts/apply_migrations.sh

lint:
	cd apps/api && uv run ruff check .

fmt:
	cd apps/api && uv run ruff format .
