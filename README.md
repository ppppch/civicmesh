# CivicGrid NYC (Local MVP)

CivicGrid NYC is a local-first implementation of AskNYC Compute.

## What is implemented in this first commit

- Monorepo scaffold for API, web app, worker simulator, and DB migrations.
- Local infra with Postgres/PostGIS, Redis, and Qdrant via Docker Compose.
- FastAPI baseline with health and version endpoints.
- Web shell with MVP surfaces: Ask NYC, Civic Compute, Insight Atlas.
- Worker simulator stub for local multi-device testing.
- Live NYC Open Data catalog ingestion endpoint with scoring + Postgres upsert.
- Dataset search endpoint over ingested catalog.
- Firebase Hosting scaffold for free public frontend domain deployment.
- Required browser-side WebGPU embedding compute before answer retrieval.
- Client-side persistence of embeddings and run outputs in IndexedDB.

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

Apply migrations:

```bash
make migrate
```

Then run in separate terminals:

```bash
make api
make web
```

API docs: http://localhost:8000/docs
Web app: http://localhost:5173

## First live API flow

1. Run `POST /ingest/catalog` to fetch and score NYC Open Data datasets.
2. Frontend runs local WebGPU embedding inference (Transformers.js) for query and candidate rows.
3. Frontend calls `GET /datasets/search?query=...` then locally reranks by cosine similarity.

## Zero-cloud compute mode

- Inference location: browser only (WebGPU required).
- Embedding storage: browser IndexedDB database `civicgrid-local`, store `embeddings`.
- Local run/output storage: browser IndexedDB database `civicgrid-local`, store `runs`.
- Cloud usage: Firebase Hosting serves static app; API/cloud stores metadata and dataset catalog only.

## Firebase Hosting deployment (free domain)

1. Install Firebase CLI and login.
2. Set your Firebase project in `.firebaserc`.
3. Set production API URL in `apps/web/.env` (`VITE_API_BASE_URL`).
4. Deploy:

```bash
./scripts/deploy_firebase.sh
```

## Next implementation targets

- Socrata ingestion pipeline and normalized dataset catalog.
- Embedding pipeline + hybrid retrieval.
- Deterministic planner and work-unit scheduler.
- Consensus verification and reproducible insight cards.
