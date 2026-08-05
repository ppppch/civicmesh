#!/usr/bin/env python3
"""Compare ONNX model predictions against a naive baseline using real Firestore records.

The naive baseline predicts that next year's complaint count equals the
current year's count (counts.current in the embedding record).

Run from repo root:
    uv run --project apps/api python scripts/baseline_comparison.py
"""

from __future__ import annotations

import base64
import json
import math
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import numpy as np
import onnxruntime as ort


MODEL_DIR = Path(__file__).resolve().parents[1] / "public" / "models" / "forecast311" / "v1"
FIXTURES_PATH = MODEL_DIR / "parity-fixtures.json"
MODEL_CARD_PATH = MODEL_DIR / "model-card.json"
ENV_PATH = Path(__file__).resolve().parents[1] / "apps" / "web" / ".env"

PROJECT_ID = "civicgrid-e8b69"
RELEASE_ID = "20260728-164958"
DATABASE_ID = "nycdata"

# Test a range of real combinations from Firestore.
TEST_COMBINATIONS = [
    ("10025", "heat/hot water"),
    ("10025", "Street Condition"),
    ("10000", "HEAT/HOT WATER"),
    ("10001", "HEAT/HOT WATER"),
    ("10002", "Street Condition"),
    ("10003", "HEAT/HOT WATER"),
]


def load_api_key() -> str:
    if ENV_PATH.exists():
        match = re.search(r'^VITE_FIREBASE_API_KEY=(.+)$', ENV_PATH.read_text(), re.MULTILINE)
        if match:
            return match.group(1).strip()
    key = os.environ.get("VITE_FIREBASE_API_KEY", "")
    if key:
        return key
    raise RuntimeError("VITE_FIREBASE_API_KEY not found in apps/web/.env or environment")


def normalize_complaint_type(complaint_type: str) -> str:
    return complaint_type.strip().lower()


def build_record_id(source_year: int, zipcode: str, complaint_type: str) -> str:
    import hashlib
    normalized = normalize_complaint_type(complaint_type)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{source_year}_{zipcode}_{digest[:16]}"


def parse_value(value_obj: dict):
    """Convert Firestore REST API value objects to Python types."""
    if "stringValue" in value_obj:
        return value_obj["stringValue"]
    if "integerValue" in value_obj:
        return int(value_obj["integerValue"])
    if "doubleValue" in value_obj:
        return float(value_obj["doubleValue"])
    if "booleanValue" in value_obj:
        return bool(value_obj["booleanValue"])
    if "arrayValue" in value_obj:
        return [parse_value(v) for v in value_obj["arrayValue"].get("values", [])]
    if "mapValue" in value_obj:
        return {k: parse_value(v) for k, v in value_obj["mapValue"].get("fields", {}).items()}
    return None


def decode_embedding(embedding: dict) -> list[float]:
    """Decode an int8-scale base64 embedding into floats."""
    dimension = embedding["dimension"]
    scale = embedding["scale"]
    values_base64 = embedding["values_base64"]

    raw_bytes = base64.b64decode(values_base64)
    int8_values = list(raw_bytes)

    if len(int8_values) != dimension:
        raise ValueError(f"Decoded embedding dimension mismatch: {len(int8_values)} != {dimension}")

    # Convert unsigned byte values back to signed int8, then scale.
    return [((v - 256) if v > 127 else v) * scale for v in int8_values]


def fetch_record(zipcode: str, complaint_type: str) -> dict:
    api_key = load_api_key()
    record_id = build_record_id(2025, zipcode, complaint_type)
    document_path = f"forecast_releases/{RELEASE_ID}/embedding_records/{record_id}"
    url = (
        f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/"
        f"databases/{DATABASE_ID}/documents/{document_path}?key={api_key}"
    )

    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"Record not found: {zipcode} / {complaint_type}") from exc
        raise RuntimeError(f"Firestore request failed: {exc.code}") from exc

    return {k: parse_value(v) for k, v in data.get("fields", {}).items()}


def build_feature_vector(record: dict) -> list[float]:
    """Build the same feature vector the frontend uses."""
    counts = record["counts"]
    trends = record["trend_features"]
    embedding = decode_embedding(record["embedding"])

    return [
        counts["current"],
        counts["lag_1"],
        counts["lag_2"],
        trends[0],
        trends[1],
        trends[2],
        *embedding,
    ]


def compute_baselines(record: dict) -> dict[str, float]:
    """Compute simple baseline predictions from the record.

    Trend features are [current - lag_1, lag_1 - lag_2, mean(current, lag_1, lag_2)],
    per public/models/forecast311/v1/feature-schema.json.
    """
    counts = record["counts"]
    current = counts["current"]
    lag_1 = counts["lag_1"]
    lag_2 = counts["lag_2"]

    return {
        "naive_current": current,
        "moving_avg_3yr": (current + lag_1 + lag_2) / 3,
        "naive_with_trend": current + (current - lag_1),
    }


def load_model_card() -> dict:
    with MODEL_CARD_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def run_model(onnx_file: str, input_vector: list[float]) -> tuple[float, float]:
    """Run an ONNX model and return (raw_prediction, clamped_prediction)."""
    session = ort.InferenceSession(
        str(MODEL_DIR / onnx_file),
        providers=["CPUExecutionProvider"],
    )
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: np.array(input_vector, dtype=np.float32).reshape(1, -1)})
    raw = float(outputs[0].flatten()[0])
    clamped = float(np.maximum(0, raw))
    return raw, clamped


def main() -> int:
    model_card = load_model_card()
    models = {m["model_name"]: m for m in model_card["models"]}

    print("Real Firestore Record Baseline Comparison")
    print("=" * 110)

    for zipcode, complaint_type in TEST_COMBINATIONS:
        print(f"\nCombination: {zipcode} / {complaint_type}")
        print("-" * 110)

        try:
            record = fetch_record(zipcode, complaint_type)
        except RuntimeError as exc:
            print(f"  Error: {exc}")
            continue

        feature_vector = build_feature_vector(record)
        baselines = compute_baselines(record)

        print(f"  Feature vector length: {len(feature_vector)}")
        print(f"  {'Baseline':<20} {'Value':<12}")
        print(f"  {'-'*20} {'-'*12}")
        for name, value in baselines.items():
            print(f"  {name:<20} {value:<12.2f}")

        print(f"\n  {'Model':<15} {'Raw':<12} {'Clamped':<12} {'vs Naive':<12} {'vs MovAvg':<12} {'vs Trend':<12} {'Card MAE':<12}")
        print(f"  {'-'*15} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

        for model_name, model_meta in models.items():
            raw, prediction = run_model(model_meta["onnx_file"], feature_vector)
            print(
                f"  {model_name:<15} "
                f"{raw:<12.2f} "
                f"{prediction:<12.2f} "
                f"{prediction - baselines['naive_current']:<+12.2f} "
                f"{prediction - baselines['moving_avg_3yr']:<+12.2f} "
                f"{prediction - baselines['naive_with_trend']:<+12.2f} "
                f"{model_meta['mae']:<12.2f}"
            )

    print("\n" + "=" * 110)
    print("Notes:")
    print("- 'naive_current' baseline: next year = current year's count.")
    print("- 'moving_avg_3yr' baseline: average of current, lag_1, and lag_2 counts.")
    print("- 'naive_with_trend' baseline: current year + recent year-over-year change.")
    print("- 'Raw' is the ONNX model output before clamping.")
    print("- 'Clamped' is max(0, raw), matching the frontend behavior.")
    print("- 'vs *' columns show how much the clamped prediction differs from each baseline.")
    print("- 'Card MAE' is the validation MAE reported in model-card.json.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
