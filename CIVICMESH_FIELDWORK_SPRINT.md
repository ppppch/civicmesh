# CivicMesh Fieldwork Sprint

Week of: 2026-08-04
Time commitment: 25 hours per intern
Schedule: 5 hours per day for 5 days

## Goal For The Week

Move the deployed 311 forecasting workflow toward a reliable public release. The local ONNX forecast works, but the live selector currently falls back to a small mock dataset, model quality needs stronger evidence, and browser release coverage is missing.

Each intern should be assigned one track below. Every track totals exactly 25 hours and ends with a reviewed pull request or research report. Do not combine unfinished pieces from multiple tracks.

## Current Starting Point

- Work from the latest `main` branch.
- Run `npm --prefix apps/web ci`, `npm --prefix apps/web test`, and `npm --prefix apps/web run build` before making changes.
- The active frontend release is `20260729-022708`.
- Real forecasts use the `nycdata` Firestore database and local ONNX models.
- The deployed featured-dataset request falls through to `http://localhost:8000` and loads the bundled mock dataset.
- The Firestore release contains 300 valid ZIP and complaint-type records, but the live selector exposes only two ZIP codes.
- Do not commit `.env` files, credentials, downloaded production data, or generated build directories.

## Track A: Frontend And Release Data

Best for an intern working in React, TypeScript, Firebase, or product UI.

### Monday: Reproduce And Document - 5 Hours

1. Run the web app and confirm the test/build baseline - 1 hour.
2. Reproduce the production mock fallback and capture the request path and UI state - 1.5 hours.
3. Trace how `getFeaturedDataset`, Firestore, and the forecast selectors exchange data - 1.5 hours.
4. Write a short implementation proposal comparing a Firestore selector manifest with a bundled versioned manifest - 1 hour.

Deliverable: a one-page proposal added to the pull request description.

### Tuesday: Selector Data Source - 5 Hours

1. Implement the approved selector-manifest reader - 3 hours.
2. Populate ZIP and complaint-type controls from valid release combinations - 1 hour.
3. Add loading, empty, and unavailable-release states - 1 hour.

Deliverable: all valid release combinations can be represented without using the featured demo dataset.

### Wednesday: Production Behavior - 5 Hours

1. Prevent production from requesting `localhost` - 1.5 hours.
2. Restrict mock data to an explicit development/test mode - 1.5 hours.
3. Display release ID, combination count, and live/mock status near the selectors - 1 hour.
4. Check keyboard navigation and visible focus states - 1 hour.

Deliverable: production failures are visible and never silently presented as real data.

### Thursday: Tests And Responsive QA - 5 Hours

1. Add unit tests for manifest success, missing manifest, and invalid data - 2 hours.
2. Test ZIP/type pairing and prevent invalid cross-product selections - 1 hour.
3. Check the forecast workspace at 390 px, 768 px, and 1440 px widths - 1 hour.
4. Fix any overflow, overlap, or unreadable status text found during testing - 1 hour.

Deliverable: focused tests and desktop/mobile screenshots in the pull request.

### Friday: Validation And Handoff - 5 Hours

1. Run the full web tests and production build - 1 hour.
2. Verify forecast results for all three models using one known record - 1 hour.
3. Confirm that no forecast action calls a backend inference endpoint - 1 hour.
4. Update relevant setup and behavior documentation - 1 hour.
5. Prepare a five-minute demo and respond to review feedback - 1 hour.

Done when: the full release is selectable, production makes no localhost request, tests pass, and the pull request contains evidence.

## Track B: Model And Data Research

Best for an intern working in Python, data science, statistics, or model evaluation.

### Monday: Data And Method Audit - 5 Hours

1. Read the feature schema, release builder, training script, and model card - 2 hours.
2. Document the train/validation split and identify leakage or imputation risks - 1.5 hours.
3. List unresolved `DRAFT`, `TBD`, taxonomy, and ZIP-normalization decisions - 1.5 hours.

Deliverable: a concise audit with questions that require data-steward approval.

### Tuesday: Baseline Forecasts - 5 Hours

1. Implement a naive persistence baseline where next year equals the current year - 2 hours.
2. Add seasonal trend or moving-average baselines where the data supports them - 1.5 hours.
3. Calculate MAE, RMSE, median absolute error, and weighted absolute percentage error - 1.5 hours.

Deliverable: reproducible baseline metrics, not a notebook-only result.

### Wednesday: Temporal Backtesting - 5 Hours

1. Run rolling year-pair backtests instead of only a 2024-to-2025 holdout - 3 hours.
2. Compare Random Forest, XGBoost, LightGBM, and naive baselines - 1 hour.
3. Record runtime, row counts, random seeds, and artifact versions - 1 hour.

Deliverable: machine-readable results plus a small summary table.

### Thursday: Segment And Failure Analysis - 5 Hours

1. Break metrics down by complaint type, ZIP, and complaint-volume band - 2 hours.
2. Investigate XGBoost's train/validation gap - 1 hour.
3. Investigate LightGBM zero or negative predictions - 1 hour.
4. Identify the ten largest absolute errors for domain review - 1 hour.

Deliverable: a failure-analysis report with examples and likely causes.

### Friday: Recommendation And Handoff - 5 Hours

1. Run an ablation with and without the deterministic hash embedding - 2 hours.
2. Recommend a default model only if it beats the approved baseline - 1 hour.
3. Document limitations, uncertainty needs, and proposed next experiments - 1 hour.
4. Prepare a five-minute review and respond to feedback - 1 hour.

Done when: another contributor can reproduce the evaluation and understand whether any model meaningfully beats a simple baseline.

## Track C: Browser QA, Security, And Performance

Best for an intern working in testing, web reliability, security, or performance.

### Monday: Test Plan And Setup - 5 Hours

1. Map the forecast happy path and existing unit coverage - 1.5 hours.
2. Propose Playwright coverage and Firebase Emulator usage - 1.5 hours.
3. Add the approved browser-test configuration and one smoke test - 2 hours.

Deliverable: a browser test that runs locally with documented prerequisites.

### Tuesday: Release Flow Coverage - 5 Hours

1. Test ZIP, complaint type, and model selection - 2 hours.
2. Assert prediction, metrics, caveat, release ID, and provenance - 2 hours.
3. Confirm the forecast flow makes no backend inference request - 1 hour.

Deliverable: deterministic happy-path browser coverage.

### Wednesday: Failure And Cache Coverage - 5 Hours

1. Cover missing Firestore records and unavailable Firestore - 1.5 hours.
2. Cover checksum, feature-schema, embedding-version, and missing-model failures - 2 hours.
3. Verify a cache hit avoids a second Firestore record read - 1.5 hours.

Deliverable: clear failure assertions without depending on production outages.

### Thursday: Dependency And Performance Audit - 5 Hours

1. Analyze production `npm audit` findings and affected runtime paths - 1.5 hours.
2. Research supported Firebase and Transformers upgrade paths - 1.5 hours.
3. Measure initial JavaScript, WASM, model load, cold inference, and warm inference - 1.5 hours.
4. Recommend size and latency budgets - 0.5 hour.

Deliverable: prioritized findings; do not run `npm audit fix --force`.

### Friday: CI And Handoff - 5 Hours

1. Add the approved browser smoke test to CI - 2 hours.
2. Capture desktop and mobile screenshots and check for overlap - 1 hour.
3. Run tests/build and document exact commands and results - 1 hour.
4. Prepare a five-minute demo and respond to review feedback - 1 hour.

Done when: the main release flow has browser evidence, known failures are reproducible, and performance/security recommendations are actionable.

## Rules For Every Intern

1. Create a branch from current `main`; do not commit directly to `main`.
2. Keep commits focused and use a pull request for review.
3. Record actual time by task. Raise scope problems before exceeding 25 hours.
4. Add tests for changed behavior and include the commands run in the pull request.
5. Do not deploy Firebase, alter Firestore rules, publish a release, or rotate dependencies without supervisor approval.
6. Do not use production service-account credentials or include secrets in screenshots, logs, issues, or commits.
7. Do not claim model improvement without comparing against a reproducible baseline.
8. Stop and ask the supervisor when a task requires a product, data-governance, security, or deployment decision.

## Friday Supervisor Review

Use this checklist for each intern:

- Actual hours total 25 or less.
- Required artifact or pull request is linked.
- Tests and build results are included.
- Research claims are supported by data or source references.
- No credentials, environment files, or generated artifacts are committed.
- Remaining risks and decisions are stated plainly.
- The next task is small enough for another 25-hour week.
