# Model and Data Research Report

**Author:** Ritika Subedi  
**Branch:** `ritika/week2-model-research`  
**Release ID tested:** `20260728-164958`  
**Date:** 2026-08-04

---

## 1. Scope

This report evaluates the three ONNX forecasting models shipped with the CivicGrid NYC web frontend:

- Random Forest
- XGBoost
- LightGBM

The goal is to compare their predictions against simple baselines, document model-specific behavior, and provide a data-supported recommendation for the default model.

---

## 2. Models and Baselines

### Models

| Model | Validation MAE | Validation RMSE | Training MAE | Training RMSE |
|-------|---------------:|----------------:|-------------:|--------------:|
| random_forest | 292.74 | 743.55 | 84.48 | 231.28 |
| xgboost | 303.93 | 753.39 | 4.99 | 6.83 |
| lightgbm | 301.26 | 679.47 | 66.78 | 254.09 |

Source: `public/models/forecast311/v1/model-card.json`

**Overfitting observation:** XGBoost has an extremely low training MAE (4.99) but a high validation MAE (303.93), suggesting it memorized the training data and may not generalize as well as the other models.

### Baselines

Three simple baselines were computed from each embedding record:

| Baseline | Formula |
|----------|---------|
| naive_current | `counts.current` |
| moving_avg_3yr | `(current + lag_1 + lag_2) / 3` |
| naive_with_trend | `current + (current - lag_1)` |

The trend features in the record are defined as `[current - lag_1, lag_1 - lag_2, mean(current, lag_1, lag_2)]` per `public/models/forecast311/v1/feature-schema.json`.

---

## 3. Methodology

1. Loaded the ONNX models using `onnxruntime`.
2. Fetched real embedding records from Firestore (`nycdata` database, release `20260728-164958`).
3. Built the same 38-dimensional feature vector used by the frontend.
4. Ran each model and recorded both raw and clamped predictions.
5. Computed each baseline from the record's counts.
6. Compared model predictions to each baseline.

Script: `scripts/baseline_comparison.py`

Command run:

```bash
uv run --project apps/api python scripts/baseline_comparison.py
```

---

## 4. Results

### Parity Fixture Verification

All three models produced predictions matching `parity-fixtures.json` within tolerance:

| Model | Expected | Actual | Tolerance |
|-------|---------:|-------:|----------:|
| random_forest | 22.8383 | 22.8384 | 0.01 |
| xgboost | 22.1504 | 22.1505 | 0.01 |
| lightgbm | 24.8443 | 24.8442 | 0.01 |

### Real Firestore Records

Six ZIP-code and complaint-type combinations were tested:

| ZIP | Complaint Type | Current | Moving Avg | Naive w/ Trend |
|-----|----------------|--------:|-----------:|---------------:|
| 10025 | heat/hot water | 3439 | 3124.33 | 3797.00 |
| 10025 | Street Condition | 508 | 545.00 | 448.00 |
| 10000 | HEAT/HOT WATER | 1 | 1.00 | 1.00 |
| 10001 | HEAT/HOT WATER | 383 | 388.00 | 324.00 |
| 10002 | Street Condition | 450 | 431.67 | 426.00 |
| 10003 | HEAT/HOT WATER | 1733 | 1090.00 | 1955.00 |

### Model Predictions vs Baselines

| ZIP | Type | Model | Prediction | vs Naive | vs MovAvg | vs Trend |
|-----|------|-------|-----------:|---------:|----------:|---------:|
| 10025 | heat/hot water | random_forest | 2781.27 | −657.73 | −343.07 | −1015.73 |
| 10025 | heat/hot water | xgboost | 1626.91 | −1812.09 | −1497.43 | −2170.09 |
| 10025 | heat/hot water | lightgbm | 2130.47 | −1308.53 | −993.86 | −1666.53 |
| 10025 | Street Condition | random_forest | 615.77 | +107.77 | +70.77 | +167.77 |
| 10025 | Street Condition | xgboost | 637.19 | +129.19 | +92.19 | +189.19 |
| 10025 | Street Condition | lightgbm | 618.33 | +110.33 | +73.33 | +170.33 |
| 10000 | HEAT/HOT WATER | random_forest | 6.77 | +5.77 | +5.77 | +5.77 |
| 10000 | HEAT/HOT WATER | xgboost | 23.32 | +22.32 | +22.32 | +22.32 |
| 10000 | HEAT/HOT WATER | lightgbm | 29.06 | +28.06 | +28.06 | +28.06 |
| 10001 | HEAT/HOT WATER | random_forest | 406.50 | +23.50 | +18.50 | +82.50 |
| 10001 | HEAT/HOT WATER | xgboost | 433.08 | +50.08 | +45.08 | +109.08 |
| 10001 | HEAT/HOT WATER | lightgbm | 426.19 | +43.19 | +38.19 | +102.19 |
| 10002 | Street Condition | random_forest | 392.74 | −57.26 | −38.93 | −33.26 |
| 10002 | Street Condition | xgboost | 379.86 | −70.14 | −51.80 | −46.14 |
| 10002 | Street Condition | lightgbm | 379.64 | −70.36 | −52.03 | −46.36 |
| 10003 | HEAT/HOT WATER | random_forest | 972.20 | −760.80 | −117.80 | −982.80 |
| 10003 | HEAT/HOT WATER | xgboost | 889.13 | −843.87 | −200.87 | −1065.87 |
| 10003 | HEAT/HOT WATER | lightgbm | 1378.65 | −354.35 | +288.65 | −576.35 |

---

## 5. Key Findings

### 5.1 No negative raw predictions

Raw ONNX outputs and clamped outputs (`Math.max(0, raw)`) were identical for all 18 test cases. The frontend's negative-value clamping is a safety measure but did not activate here.

### 5.2 Models agree on direction within each combination

For every ZIP/type combination, all three models predicted the same direction relative to baselines (increase or decrease). However, the direction varied across combinations.

### 5.3 XGBoost is the most volatile

XGBoost produced both the lowest prediction (10025 heat/hot water: 1626.91) and among the highest (10001 heat/hot water: 433.08, 10025 street condition: 637.19). Its large gap between training MAE (4.99) and validation MAE (303.93) suggests overfitting.

### 5.4 LightGBM has the widest prediction range

For 10003 heat/hot water, LightGBM predicted 1378.65 while XGBoost predicted 889.13 — a difference of 489.52 complaints (55% higher).

### 5.5 Random Forest is the most conservative

Random Forest predictions were generally closest to the center of the three models and closest to the moving-average baseline.

### 5.6 Baseline comparison is mixed

No model consistently beats all baselines across all combinations. For example:
- 10025 heat/hot water: all models predict far below `naive_current` and `naive_with_trend`.
- 10003 heat/hot water: LightGBM predicts above `moving_avg_3yr` but below `naive_current`.
- 10000 heat/hot water: all models predict well above all baselines.

Without actual 2026 ground-truth data, it is impossible to declare one model universally best. The validation MAE from the model card remains the best available summary metric.

---

## 5.5 Hash-Embedding Ablation

A separate ablation study (`scripts/embedding_ablation.py`) ran each model twice per record:

1. **Full vector**: counts + trends + 32-dimensional hash embedding
2. **No embedding**: counts + trends + 32 zeros

### Notable results

| Combination | Model | Full Prediction | No Embedding | % Change |
|-------------|-------|----------------:|-------------:|---------:|
| 10000 / HEAT/HOT WATER | lightgbm | 29.06 | 3.70 | **+685%** |
| 10003 / HEAT/HOT WATER | xgboost | 889.13 | 1384.25 | **−35.8%** |
| 10003 / HEAT/HOT WATER | random_forest | 972.20 | 1291.16 | **−24.7%** |
| 10025 / heat/hot water | xgboost | 1626.91 | 1960.11 | **−17.0%** |

### Interpretation

- The hash embedding is **not noise**. Removing it changes predictions substantially in many cases.
- **XGBoost is the most sensitive** to the embedding, with changes up to −35.8%.
- **LightGBM shows the most extreme relative change** for low-volume records (10000: +685%), but this is partly because the baseline prediction without embedding is very small (3.70).
- In a few cases (e.g., 10025 Street Condition with XGBoost), the embedding has almost no effect (+0.6%).

This suggests the embedding carries meaningful signal for the models, but its influence is inconsistent across ZIP codes, complaint types, and model variants.

---

## 6. Security and Performance Review

### 6.1 npm Audit Findings

Command run:

```bash
cd apps/web
npm audit
```

Result:

```text
18 vulnerabilities (10 moderate, 6 high, 2 critical)
```

| Severity | Package | Impact | Affected Path |
|----------|---------|--------|---------------|
| Critical | protobufjs | Arbitrary code execution, code injection, DoS | onnxruntime-web → @xenova/transformers |
| Critical | websocket-driver | Resource limit bypass, message corruption | Firebase realtime features |
| High | sharp | libvips CVEs | @xenova/transformers |
| High | undici | HTTP/WebSocket smuggling, DoS, header injection | firebase → @firebase/auth/firestore/functions/storage |
| Moderate | esbuild | Dev-server CORS issue | vite (build-time only) |

### Why these are not auto-fixed

Running `npm audit fix --force` would upgrade:

- Vite to 8.x (breaking)
- Firebase to 12.x (breaking)
- @xenova/transformers to 1.4.2 (breaking)

Project rules require supervisor approval before rotating dependencies. These upgrades should be reviewed and tested in a separate PR.

### Risk assessment

- **esbuild** is a build-time dependency. The vulnerability only affects the Vite dev server, not production users.
- **protobufjs, sharp, undici, websocket-driver** are runtime dependencies used by the ONNX runtime, transformers library, and Firebase SDK. These affect deployed users and should be prioritized.
- No production service-account credentials are used in the frontend. Firebase reads rely on public Firestore rules and the web API key.

### 6.2 Performance Observations

Production build output:

```text
dist/assets/ort-wasm-simd-threaded.jsep-DC5y_g6C.wasm  26,827.54 kB
dist/assets/index-C54EUSRM.css                              2.13 kB │ gzip:   0.89 kB
dist/assets/index-Ce5Ued16.js                           1,894.02 kB │ gzip: 472.77 kB
```

- The ONNX Runtime WebAssembly file is **~26 MB**, which is large for mobile or slow connections.
- The main JavaScript bundle is **~1.9 MB** (~472 kB gzipped).
- Vite warns that some chunks exceed 500 kB after minification.

### 6.3 Recommendations

1. **Dependency upgrades:** Schedule supervised upgrades for Firebase, Vite, and @xenova/transformers.
2. **WASM loading:** Consider lazy-loading ONNX Runtime only when the forecast tab is used.
3. **Bundle splitting:** Use dynamic imports to split the application and reduce initial load.
4. **Latency budget:** Target < 3 seconds to first meaningful paint on a 4G connection.

A full runtime performance profile (cold vs warm inference, model load times) was not completed in this review and should be follow-up work.

### 6.4 Forecast Runtime Path Verification

The 311 forecast flow was verified to use only local inference and Firestore reads:

| Step | Source | Network Target | Local Compute? |
|------|--------|----------------|----------------|
| Fetch embedding record | `firestoreEmbeddingRepository.ts` | Firebase Firestore (`nycdata`) | No |
| Load model artifacts | `modelRegistry.ts` | Same-origin static files (`/models/forecast311/v1/`) | No |
| Run inference | `localInference.ts` | None — ONNX Runtime Web in browser | **Yes** |
| Build provenance | `provenance.ts` | None | **Yes** |

**No `localhost:8000` backend calls are made during forecast inference.**

Note: the separate "Ask NYC" dataset search feature in `apps/web/src/api.ts` still calls `http://localhost:8000` for catalog ingest and dataset search. That path is unrelated to the forecast flow.

---

## 7. Recommendation

**Do not set XGBoost as the default model.** Its extreme volatility and overfitting (training MAE 4.99 vs validation MAE 303.93) make it unreliable.

**LightGBM is a reasonable candidate** because it has the lowest validation RMSE (679.47), but its prediction range is wide.

**Random Forest is the safest conservative choice** because its predictions are usually closest to the moving-average baseline and it has the lowest validation MAE (292.74).

**Final recommendation:** Keep all three models selectable in the UI. If a default must be chosen, use **Random Forest** as the conservative default, with clear caveats that model quality varies by ZIP code and complaint type.

---

## 8. Open Questions and Risks

1. We do not have actual 2026 complaint counts, so all model comparisons are against baselines, not ground truth.
2. The hash-embedding ablation shows the embedding influences predictions, but the direction and magnitude are inconsistent across models and records. A deeper feature-importance analysis would help.
3. The `trend_features` definition was found in `feature-schema.json`; the frontend code should reference this schema explicitly to avoid confusion.
4. XGBoost overfitting should be investigated further by examining the training script and hyperparameters.
5. A rolling year-pair backtest would strengthen the model comparison if historical data is available.
6. A full runtime performance profile (cold vs warm inference, model load times) was not completed and should be follow-up work.
7. Rolling year-pair backtests were not completed because they require retraining models on historical year-pairs; this should be follow-up work if historical training data is available.

---

## 9. Commands Run

```bash
# Frontend tests and build (run on ritika/week2-model-research)
cd apps/web
npm test
npm run build
```

Test output:

```text
Test Files  1 passed (1)
Tests       5 passed (5)
```

Build output:

```text
✓ built in 1.78s
```

Note: The 5 passing tests are the existing forecast module unit tests in `apps/web/src/forecast/forecast.test.ts`. Additional tests were added on branch `ritika/forecast-tests` in the previous week.

```bash
# Baseline comparison script
uv run --project apps/api python scripts/baseline_comparison.py

# Hash-embedding ablation study
uv run --project apps/api python scripts/embedding_ablation.py

# Model parity validation
uv run --project apps/api python scripts/validate_forecast311_parity.py

# Firestore record validation
uv run --project apps/api python scripts/validate_forecast_records.py
```

---

## 10. Files Added or Modified

- `scripts/baseline_comparison.py` — compares ONNX predictions to baselines
- `scripts/embedding_ablation.py` — measures the effect of the hash embedding
- `scripts/validate_forecast311_parity.py` — validates model outputs against parity fixtures
- `scripts/validate_forecast_records.py` — validates Firestore record shape and checksums
- `MODEL_RESEARCH.md` — this report
