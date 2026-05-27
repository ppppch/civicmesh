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
- Deterministic NYC job engine with first 5 civic data-science jobs.
- Systematic generated job catalog API (10,000+ jobs from ingested NYC datasets).
- Pre-embedding artifact builder (manifest + sharded vectors).
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

## NYC jobs API

- `GET /jobs` lists available deterministic NYC job recipes.
- `POST /jobs/{job_id}/run` executes one job using live NYC Open Data signals.
- `POST /jobs/generated/build?target_count=10000` generates a large systematic job catalog.
- `GET /jobs/generated` pages generated jobs.
- `GET /jobs/generated/{job_id}` retrieves one generated job spec.

## Run publishing API

- `POST /runs/publish` publishes a client-computed run (requires bearer token).
- `GET /runs/mine` lists published runs for current bearer identity.

In local dev mode (`AUTH_MODE=dev`), any bearer token string maps directly to user id.

Current MVP job ids:

- `heat-vulnerability-zones`
- `tree-canopy-equity`
- `housing-violations-near-schools`
- `transit-accessibility-score`
- `health-environment-risk`

## Pre-embedding artifacts

- `POST /embeddings/build` builds sharded embedding artifacts and a versioned manifest from ingested datasets.
- Local script: `make build-embeddings`

## Generate 10,000 jobs

After ingesting datasets, generate and inspect the large client-executable catalog:

```bash
make generate-10k-jobs
make generated-jobs
```

These generated jobs are systematic combinations of:

- Ingested NYC datasets
- Client-capable methods (trend, rank, before/after, anomaly, joinability, equity-gap, coverage-gap)
- Civic topics (housing, heat, trees, schools, sanitation, transit, health, environment, safety)

## Flutter mobile app

Mobile app source: `apps/mobile_flutter`

Run locally (requires Flutter SDK):

```bash
cd apps/mobile_flutter
flutter create .
flutter pub get
flutter run
```

In-app, set API base URL in the top field:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://127.0.0.1:8000`
- Physical device: `http://<your-laptop-lan-ip>:8000`

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

## Firebase security model files

- Firestore rules: `firestore.rules`
- Firestore indexes: `firestore.indexes.json`
- Storage rules: `storage.rules`

Deploy these with:

```bash
firebase deploy --only firestore:rules,firestore:indexes,storage
```

## Web app auth and publish setup

Set these in `apps/web/.env`:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

Then users can sign in and publish local runs via `/runs/publish`.

## Next implementation targets

- Socrata ingestion pipeline and normalized dataset catalog.
- Embedding pipeline + hybrid retrieval.
- Deterministic planner and work-unit scheduler.
- Consensus verification and reproducible insight cards.
