# CivicGrid NYC Master Plan

## Active Simplified Scope (Current)

This repository is currently prioritizing a narrower execution path:

1. Build 2025 embeddings for NYC 311 complaint data keyed by ZIP code and complaint type.
2. Train three supervised models for next-year totals: Random Forest, XGBoost, and LightGBM.
3. Predict 2026 complaint counts for each ZIP + complaint-type pair from 2025 source rows.
4. Compare model performance with consistent MAE/RMSE metrics and keep outputs reproducible.

All other product surfaces remain optional until this forecast workflow is stable.

## Execution Order And Human Gates

### Phase A (Web-First Delivery)

1. Ship web ingestion/import UX for 311 yearly counts.
2. Ship web-triggered training/inference against /forecast311/train-and-predict.
3. Ship model comparison leaderboard (Random Forest, XGBoost, LightGBM).
4. Ship ZIP + complaint forecast explorer for 2026 predictions.

Human gates in Phase A:

1. Data steward approves final 2025 cleanup rules before training runs.
2. Product owner approves MAE/RMSE success thresholds.
3. Domain reviewer signs off that top forecasts are plausible and caveated.

### Phase B (Flutter + ONNX + Swift Bridge)

1. Lock web schema and feature contract.
2. Export candidate model artifacts to ONNX.
3. Implement Swift ONNX runtime bridge and expose Flutter bindings.
4. Recreate web forecasting UX in Flutter with matching filters/metrics.
5. Run parity testing against web baseline outputs.

Human gates in Phase B:

1. Mobile engineer validates bridge memory/performance on target iOS devices.
2. QA validates parity tolerances and edge-case behavior.
3. Release owner approves mobile rollout after manual exploratory testing.

## 1. Vision And Non-Negotiables

CivicGrid NYC is a zero-cloud-inference civic intelligence platform:

- All user job execution and model inference run on user devices in browser.
- Cloud is used for hosting static artifacts, metadata, auth, and published outputs.
- Every result must be reproducible, versioned, and traceable to source data.
- NYC Open Data is the only data source for MVP.

Non-negotiable constraints:

- No opaque server-side answer generation for user jobs.
- No arbitrary code execution on user devices.
- Every public result includes caveats, provenance, and model/data version info.

---

## 2. Product Scope

### 2.1 MVP Product Surfaces

1. Ask NYC
- Search and select relevant datasets.
- Run local compute pipeline.
- Show ranked datasets and local run outputs.

2. Jobs
- Browse deterministic job templates.
- Run one-click jobs locally.
- Publish validated run artifacts.

3. Insight Atlas
- Browse public published run summaries.
- Filter by topic, method, geography, and confidence.

4. Civic Compute
- Show user contribution stats.
- Show local model/runtime activity and verification status.

### 2.2 User Roles

1. Visitor
- Can browse public insights and docs.

2. Authenticated User
- Can run jobs locally and publish output artifacts.

3. Operator/Admin
- Manages embedding versions, model versions, and job template publishing.

---

## 3. System Architecture

### 3.1 Components

1. Web App (Vite + React)
- Local inference runtime.
- IndexedDB caching for embeddings and local runs.
- Firebase Auth sign-in.

2. API (FastAPI)
- NYC Open Data ingestion.
- Job catalog generation and deterministic job execution helpers.
- Run publish validation and storage.
- Embedding artifact manifest generation.

3. Databases
- Postgres for metadata catalog, generated jobs, published runs.
- IndexedDB in browser for local embeddings and local run history.

4. Firebase
- Hosting for web app static assets.
- Storage for model and embedding artifact shards.
- Firestore for config docs, optional public run feed mirror.
- Auth for user identity.

5. Optional Compute Controls
- Local worker simulation for verification logic.

### 3.2 Data Flow

1. Operator ingests NYC datasets into Postgres catalog.
2. Operator runs laptop pre-embedding pipeline.
3. Embedding shards + manifest uploaded to Firebase Storage.
4. Web client reads active embedding version and downloads needed shards.
5. User signs in and chooses a job.
6. User device runs embeddings/rerank/job calculations locally.
7. User publishes run to API endpoint.
8. API validates payload and stores summary/provenance.
9. Public atlas reads published summaries.

---

## 4. Data Model Plan

### 4.1 Postgres Tables

Already present:

- datasets_metadata
- work_units
- work_unit_results
- work_unit_consensus
- job_run_artifacts
- embedding_build_manifests
- generated_jobs
- published_runs

Still needed:

1. dataset_profiles
- per-column stats, null rates, type hints, geo/time hints.

2. embedding_artifacts
- artifact version metadata, checksum, publish timestamp, active flag.

3. job_templates
- curated deterministic templates separate from generated jobs.

4. run_verification
- consensus and gold-task outcomes for published runs.

### 4.2 Firebase Model

1. Firestore docs
- config/active_embedding_version
- config/active_model_versions
- jobs/{job_id} (optional mirror for client-first reads)
- runs/{run_id} public summaries
- users/{uid}/runs/{run_id} private detailed records

2. Storage paths
- embeddings/{version}/manifest.json
- embeddings/{version}/shards/*.jsonl.gz or parquet
- models/{version}/*
- run_artifacts/{uid}/{run_id}/*

---

## 5. Security, Trust, And Compliance

### 5.1 Auth

1. Firebase Auth required for run publishing.
2. API must verify Firebase ID token in production mode.
3. Dev mode token passthrough only in local.

### 5.2 Storage Rules

1. embeddings and models read-only.
2. run_artifacts user-owned write/read.
3. Public run summaries immutable except admin moderation path.

### 5.3 Result Integrity

1. Idempotency keys for publish requests.
2. Input hashes for reproducibility.
3. Model version, embedding version, job version mandatory fields.

### 5.4 Safety

1. Deny sensitive/personal targeting outputs.
2. Aggregate-only outputs.
3. Small-cell suppression rules for public results.
4. Enforced caveat sections in all published summaries.

---

## 6. Client-Side Compute Plan

### 6.1 Runtime

1. Primary: WebGPU inference path.
2. Optional fallback: WASM behind explicit policy flag.

### 6.2 Model Registry

1. Embedding model (query + local text chunk processing).
2. Reranker model.
3. Optional classifier/anomaly models.

### 6.3 Local Stores (IndexedDB)

1. embeddings store.
2. runs store.
3. model registry metadata store.
4. shard version/cache store.

### 6.4 Local Job Run Contract

Every run payload must include:

- run_id
- user_id (from auth context)
- question
- selected job id
- model_name and model_version
- embedding_artifact_version
- selected_dataset_ids
- result rows/metrics
- caveats
- reproducibility token
- timestamps and runtime metrics

---

## 7. Job System Plan

### 7.1 Curated Jobs

Keep and harden MVP 5:

- heat-vulnerability-zones
- tree-canopy-equity
- housing-violations-near-schools
- transit-accessibility-score
- health-environment-risk

### 7.2 Generated Jobs

Current goal: 10,000 generated jobs from ingested NYC catalog.

Generator dimensions:

- method templates
- civic topics
- dataset combinations
- deterministic IDs and payload schema

### 7.3 Execution Categories

1. Deterministic aggregate jobs.
2. Joinability and schema verification jobs.
3. Local rerank/scoring jobs.
4. Validation jobs for claim checks.

### 7.4 Verification

1. Replica reruns (N users/devices).
2. Consensus scoring.
3. Gold task checks.
4. Publish confidence tier labels.

---

## 8. Data Ingestion And Pre-Embedding Plan

### 8.1 Ingestion

1. Pull from Socrata catalog and dataset metadata.
2. Normalize schema and categories.
3. Persist top K selected datasets.
4. Track ingest run IDs.

### 8.2 Pre-Embedding On Laptop

1. Select corpus subset (MVP 60-150 datasets first).
2. Build text chunks (title, full description, columns, samples, geo hints).
3. Embed locally using fixed model.
4. Shard/compress and write manifest.
5. Upload artifacts to Firebase Storage.
6. Update active version pointer in config.

### 8.3 Refresh Cadence

1. Daily metadata ingest.
2. Weekly embedding refresh (or on-demand for demo).
3. Delta-only refresh for changed datasets.

---

## 9. API Roadmap

### 9.1 Existing Core Endpoints

- /ingest/catalog
- /datasets/search
- /jobs
- /jobs/{job_id}/run
- /jobs/generated/build
- /jobs/generated
- /jobs/generated/{job_id}
- /embeddings/build
- /runs/publish
- /runs/mine

### 9.2 Additions Needed

1. /config/active-embedding-version
2. /artifacts/embedding-manifest/{version}
3. /artifacts/model-manifest/{version}
4. /runs/public (paginated public atlas)
5. /runs/{run_id} (public detail)
6. /admin/artifacts/activate (protected)

### 9.3 Production Hardening

1. Token verification via firebase-admin.
2. Rate limiting and abuse controls.
3. Structured validation errors.
4. Request/response schema versioning.

---

## 10. Frontend Roadmap

### 10.1 Current Web App Improvements

1. Add route-based pages (Ask, Jobs, Atlas, Compute, Profile).
2. Add signed-in state and profile page.
3. Add generated-jobs browser with filtering and pagination.
4. Add run publish queue and retry.
5. Add atlas public run explorer.

### 10.2 UX Requirements

1. Show clear compute state (ready/downloading model/running/published).
2. Show cost/energy hints for local runs.
3. Show full provenance with expandable details.
4. Explain caveats and confidence clearly.

---

## 11. Firebase Deployment Plan

### 11.1 Hosting

1. Build web app to apps/web/dist.
2. Deploy Firebase Hosting.
3. Configure SPA rewrites.

### 11.2 Rules/Indexes

1. Deploy firestore.rules.
2. Deploy firestore.indexes.json.
3. Deploy storage.rules.

### 11.3 Environment

Web env:

- VITE_API_BASE_URL
- VITE_FIREBASE_API_KEY
- VITE_FIREBASE_AUTH_DOMAIN
- VITE_FIREBASE_PROJECT_ID
- VITE_FIREBASE_STORAGE_BUCKET
- VITE_FIREBASE_MESSAGING_SENDER_ID
- VITE_FIREBASE_APP_ID

API env:

- AUTH_MODE
- CORS_ALLOW_ORIGINS
- DB creds
- SOCRATA settings
- EMBEDDING paths/model name

---

## 12. Infrastructure And Ops

### 12.1 Local Dev

1. Use local Postgres stack.
2. Apply migrations before API runs.
3. Build embeddings from laptop.

### 12.2 Production

1. API on Cloud Run (recommended).
2. Frontend on Firebase Hosting.
3. Artifact storage on Firebase Storage.

### 12.3 Monitoring

1. API logs and error rates.
2. Publish endpoint failure rates.
3. Artifact download/checksum failures.
4. Client telemetry (opt-in) for runtime failures.

---

## 13. Testing Strategy

### 13.1 Unit Tests

1. Job generator determinism.
2. Publish validation.
3. Embedding manifest generation.

### 13.2 Integration Tests

1. Ingest -> generate jobs -> run -> publish flow.
2. Auth token acceptance/rejection behavior.
3. Firebase rules sanity checks.

### 13.3 E2E Tests

1. Signed-in user local run and publish.
2. Public atlas visibility of published run.
3. Retry from offline queue.

### 13.4 Performance Benchmarks

1. Embedding build throughput on laptop.
2. Client local run latency per job class.
3. Publish API throughput and tail latency.

---

## 14. Release Plan

### Phase A (Stabilize Existing)

- Fix ingestion reliability and schema normalization.
- Production auth verification.
- Clean generated jobs browsing.

### Phase B (End-To-End Publish)

- Signed-in local run -> publish -> atlas listing.
- Provenance and confidence badges.

### Phase C (Scale + 10k)

- Generate and index 10,000 jobs.
- Add job filters, method facets, and topic navigation.

### Phase D (Program Demo)

- Scripted 3-5 canonical NYC civic questions.
- Live run + publish + reproducibility demonstration.

---

## 15. Cost Plan

Expected cost profile with client-side compute:

1. Low traffic
- Mostly Firebase Hosting + Storage egress + minimal API costs.

2. Medium traffic
- Main growth costs: Storage/CDN egress and Firestore writes.

3. High traffic
- Add stronger caching, result compaction, and quota controls.

Cost controls:

- Cache artifacts aggressively.
- Keep public run summaries compact.
- Enforce publish quotas and dedupe.

---

## 16. Risks And Mitigations

1. WebGPU compatibility variance
- Mitigate with capability checks and optional fallback policy.

2. Data quality drift
- Mitigate with schema profiling and job caveats.

3. Abuse/spam publishing
- Mitigate with auth, rate limits, idempotency, moderation path.

4. Reproducibility drift
- Mitigate with strict version pinning and hash-based provenance.

5. Artifact mismatch
- Mitigate with checksums and activation gates.

---

## 17. Immediate Action Checklist (Execution Order)

1. Apply migrations including published_runs and generated_jobs.
2. Ingest dataset cohort and verify non-empty catalog.
3. Generate 10,000 jobs and validate pagination.
4. Run pre-embedding build on laptop and produce manifest/shards.
5. Upload embedding artifacts to Firebase Storage.
6. Add active embedding version config.
7. Configure Firebase Auth in web env.
8. Switch API from AUTH_MODE=dev to verified Firebase mode for production.
9. Execute one full signed-in run and publish.
10. Launch public atlas page for published summaries.

---

## 18. Definition Of Done

The platform is considered launch-ready when:

1. A signed-in user can run a job completely client-side.
2. The run can be published with validated schema and provenance.
3. Public users can browse published summaries with caveats and confidence.
4. Embedding artifacts are versioned, checksummed, and reproducible.
5. The system supports at least 10,000 generated jobs with working browse/filter.
6. Demo script runs successfully end-to-end without manual intervention.
