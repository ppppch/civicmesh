#!/usr/bin/env zsh
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required"
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required"
  exit 1
fi

[[ -f .env ]] || cp .env.example .env
[[ -f apps/web/.env ]] || cp apps/web/.env.example apps/web/.env

echo "Starting local infra..."
docker compose up -d

echo "Applying DB migrations..."
./scripts/apply_migrations.sh

echo "Syncing API dependencies..."
(cd apps/api && uv sync)

echo "Installing web dependencies..."
(cd apps/web && npm install)

echo "Bootstrap complete."
echo "Run: make api"
echo "Run: make web"
echo "Run: make build-embeddings"
echo "Run: make generate-10k-jobs"
