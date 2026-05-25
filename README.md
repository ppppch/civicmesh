# CivicGrid NYC (Local MVP)

CivicGrid NYC is a local-first implementation of AskNYC Compute.

## What is implemented in this first commit

- Monorepo scaffold for API, web app, worker simulator, and DB migrations.
- Local infra with Postgres/PostGIS, Redis, and Qdrant via Docker Compose.
- FastAPI baseline with health and version endpoints.
- Web shell with MVP surfaces: Ask NYC, Civic Compute, Insight Atlas.
- Worker simulator stub for local multi-device testing.

## Local prerequisites

- Docker Desktop
- Python 3.11+
- uv (https://docs.astral.sh/uv)
- Node.js 20+

## Quick start

1. Copy environment template.
2. Start infra.
3. Run API.
4. Run web app.

```bash
cp .env.example .env
docker compose up -d
cd apps/api && uv sync
cd ../web && npm install
```

Then run in separate terminals:

```bash
make api
make web
```

API docs: http://localhost:8000/docs
Web app: http://localhost:5173

## Next implementation targets

- Socrata ingestion pipeline and normalized dataset catalog.
- Embedding pipeline + hybrid retrieval.
- Deterministic planner and work-unit scheduler.
- Consensus verification and reproducible insight cards.
