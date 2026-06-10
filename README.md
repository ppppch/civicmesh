# CivicGrid NYC

CivicGrid NYC is a local-first civic forecasting platform focused on NYC 311 Open Data.

The simplified core idea is:

- Embed 2025 NYC 311 complaint signals by complaint type and ZIP code.
- Train three forecast model variants (Random Forest, XGBoost, LightGBM).
- Predict 2026 complaint totals for each complaint type in each ZIP code.
- Compare model quality side-by-side and keep predictions reproducible.

This repository is the implementation workspace for that final product.

## Simplified Product Goal

The product now centers on one forecasting workflow:

1. Build embedding features from 311 complaint rows grouped by ZIP + complaint type.
2. Train/evaluate Random Forest, XGBoost, and LightGBM on historical year-pairs.
3. Run next-year inference from 2025 rows to predict 2026 totals per ZIP + complaint type.
4. Return leaderboard metrics and per-model prediction outputs.

## Delivery Order (Explicit)

Implementation sequence is fixed:

1. Web app first (Vite/React).
2. Flutter + ONNX + Swift bridge second, after web parity is complete.

### Phase 1: Web App First

1. Connect web UI to POST /forecast311/train-and-predict.
2. Add upload/import flow for 311 yearly rows (ZIP, complaint type, year, count).
3. Run model comparison view (Random Forest, XGBoost, LightGBM) with MAE/RMSE table.
4. Add prediction table for 2026 counts by ZIP + complaint type, filterable and exportable.
5. Add reproducibility panel showing model config, source year, target year, and run timestamp.

### Phase 2: Flutter + ONNX + Swift Bridge Later

1. Freeze web model interface contract (request/response schema and feature rules).
2. Convert trained model artifacts to ONNX and validate parity against web outputs.
3. Build Swift bridge for ONNX Runtime and expose typed APIs to Flutter.
4. Implement Flutter screens matching web behavior and metrics.
5. Run parity suite to confirm Flutter predictions stay within acceptable tolerance from web baseline.

## Manual Human Tasks (Required)

The following steps cannot be fully automated and must be done by humans:

1. Select and approve the exact NYC 311 complaint taxonomy and ZIP normalization rules for 2025.
2. Verify and clean raw data edge cases (missing ZIPs, invalid ZIP formats, merged complaint labels).
3. Decide acceptance thresholds for model quality (minimum MAE/RMSE targets).
4. Review model outputs for civic reasonableness before publishing any forecast externally.
5. Approve which model variant becomes default after comparison (or keep all three visible).
6. Perform legal/policy review on public-facing forecast messaging and caveat language.
7. Run release sign-off after manual QA on key ZIP + complaint slices.

## Non-Negotiable Constraints

- No opaque server-side answer generation for user jobs.
- No arbitrary code execution on user devices.
- Every public result includes provenance, caveats, and version metadata.
- NYC Open Data is the MVP data source.

## What Exists Today

Current implementation status in this repo:

- Monorepo with API, web app, worker simulator, mobile app, and DB migrations.
- Local infrastructure via Docker Compose (Postgres/PostGIS, Redis, Qdrant).
- FastAPI service with ingestion, embedding build, and 311 forecast training/prediction endpoints.
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
- POST /forecast311/train-and-predict
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

- Harden 311 ingestion and ZIP/complaint-type normalization.
- Persist 2025 embedding artifacts and model outputs with explicit versioning.
- Add training data QA checks (missing ZIPs, sparse complaint classes, outliers).
- Add offline batch training script and reproducible model registry metadata.
- Expose simple forecast explorer views in web/mobile clients.

Reference planning document: plan.md
