# CivicGrid NYC

CivicGrid NYC is a zero-cloud-inference civic intelligence platform focused on NYC Open Data.

The core idea is simple:

- User devices do the actual model inference and civic analysis.
- Cloud services only host artifacts, metadata, auth, and published outputs.
- Every published result is reproducible, versioned, and traceable to source data.

This repository is the implementation workspace for that final product.

## Final Product Goal

The final product has four connected surfaces:

1. Ask NYC
- Ask civic questions in natural language.
- Retrieve and rerank NYC datasets against precomputed NYC corpus embeddings stored locally.
- Produce transparent, citation-ready outputs.

2. Jobs
- Browse deterministic civic job templates.
- Run jobs locally on user devices.
- Publish reproducible run artifacts.

3. Insight Atlas
- Explore public, published run summaries.
- Filter by topic, geography, method, and confidence.

4. Civic Compute
- Show contribution stats and verification status.
- Make local compute participation visible and trustworthy.

## Non-Negotiable Constraints

- No opaque server-side answer generation for user jobs.
- No arbitrary code execution on user devices.
- Every public result includes provenance, caveats, and version metadata.
- NYC Open Data is the MVP data source.

## What Exists Today

Current implementation status in this repo:

- Monorepo with API, web app, worker simulator, mobile app, and DB migrations.
- Local infrastructure via Docker Compose (Postgres/PostGIS, Redis, Qdrant).
- FastAPI service with ingestion, search, jobs, run publish, and embedding build endpoints.
- Web app (Vite + React + TypeScript) with local embedding compute and IndexedDB local run history.
- Deterministic job recipes plus generated job catalog (10,000+ target).
- Firebase Hosting/Auth scaffolding and deployment scripts.

## Embedding Strategy: Current vs Final

Current implementation (interim):

- The browser computes embeddings during interaction.
- This is useful for prototyping and validating local runtime behavior.

Final target implementation:

- Precompute embeddings for NYC Open Data offline ahead of time.
- Package and version those embedding artifacts.
- Store them locally on device (or download once and cache locally).
- Run retrieval/reranking against that local embedding store.
- Keep model artifacts local as well, versioned and reproducible.

Important nuance:

- User query processing is still done at runtime on device.
- The heavy corpus embedding step is moved to precompute pipelines.

## Architecture Overview

- Web client
	Local inference runtime and local persistence (IndexedDB).
- API
	Dataset ingestion, deterministic job helpers, artifact manifest generation, publish validation.
- Postgres
	Dataset metadata, generated jobs, published runs, and supporting artifacts.
- Firebase
	Static hosting, auth, and artifact/config distribution.

## Repository Layout

- apps/api: FastAPI backend
- apps/web: React web frontend
- apps/mobile_flutter: Flutter mobile client
- apps/worker-sim: local worker/supervisor simulator
- db/migrations: SQL migrations
- scripts: helper scripts for bootstrap, deploy, embeddings, and migrations

## Run Modes

### Frontend-Only (fastest way to see the product)

Use this when you only want to see the interface shell.

```bash
cd apps/web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open: http://127.0.0.1:5173/

Notes:

- The UI renders without Firebase credentials.
- API-backed actions (ingest/search/publish) require backend services.

### Full Local Stack

Prerequisites:

- Docker Desktop
- Python 3.11+
- uv
- Node.js 20+

Bootstrapping:

```bash
cp .env.example .env
docker compose up -d
cd apps/api && uv sync
cd ../web && npm install
cd ../..
make migrate
```

Run in separate terminals:

```bash
make api
make web
```

Endpoints:

- API docs: http://localhost:8000/docs
- Web app: http://localhost:5173

## Current API Surface

- POST /ingest/catalog
- GET /datasets/search
- GET /jobs
- POST /jobs/{job_id}/run
- POST /jobs/generated/build
- GET /jobs/generated
- GET /jobs/generated/{job_id}
- POST /embeddings/build
- POST /runs/publish
- GET /runs/mine

Current curated MVP jobs:

- heat-vulnerability-zones
- tree-canopy-equity
- housing-violations-near-schools
- transit-accessibility-score
- health-environment-risk

## Environment Configuration

Web client optional Firebase settings (apps/web/.env):

- VITE_API_BASE_URL
- VITE_FIREBASE_API_KEY
- VITE_FIREBASE_AUTH_DOMAIN
- VITE_FIREBASE_PROJECT_ID
- VITE_FIREBASE_STORAGE_BUCKET
- VITE_FIREBASE_MESSAGING_SENDER_ID
- VITE_FIREBASE_APP_ID

In local development mode, auth can be bypassed for API publishing with dev identity behavior.

## Deployment Notes

Firebase deployment helper:

```bash
./scripts/deploy_firebase.sh
```

Rules/index deployment:

```bash
firebase deploy --only firestore:rules,firestore:indexes,storage
```

## Product Roadmap (From Here To Final)

Near-term priorities:

- Harden Socrata ingestion and normalized dataset profiling.
- Complete artifact version activation flow for embeddings/models.
- Add public atlas feed endpoints and frontend explorer.
- Add verification layers (replica reruns, consensus scores, gold tasks).
- Strengthen production auth verification, rate limits, and schema versioning.

Reference planning document: plan.md
