#!/usr/bin/env python3
"""Hash-embedding ablation study.

Compares ONNX model predictions with and without the 32-dimensional
hash embedding to measure the embedding's influence on the forecast.

Run from repo root:
    uv run --project apps/api python scripts/embedding_ablation.py
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import numpy as np
import onnxruntime as ort


MODEL_DIR = Path(__file__).resolve().parents[1] / "public" / "models" / "forecast311" / "v1"
MODEL_CARD_PATH = MODEL_DIR / "model-card.json"
ENV_PATH = Path(__file__).resolve().parents[1] / "apps" / "web" / ".env"

PROJECT_ID = "civicgrid-e8b69"
RELEASE_ID = "20260728-164958"
DATABASE_ID = "nycdata"

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
    dimension = embedding["dimension"]
    scale = embedding["scale"]
    values_base64 = embedding["values_base64"]

    raw_bytes = base64.b64decode(values_base64)
    int8_values = list(raw_bytes)

    if len(int8_values) != dimension:
        raise ValueError(f"Decoded embedding dimension mismatch: {len(int8_values)} != {dimension}")

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


def build_feature_vector(record: dict, include_embedding: bool = True) -> list[float]:
    counts = record["counts"]
    trends = record["trend_features"]
    embedding = decode_embedding(record["embedding"]) if include_embedding else [0.0] * 32

    return [
        counts["current"],
        counts["lag_1"],
        counts["lag_2"],
        trends[0],
        trends[1],
        trends[2],
        *embedding,
    ]


def load_model_card() -> dict:
    with MODEL_CARD_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def run_model(onnx_file: str, input_vector: list[float]) -> float:
    session = ort.InferenceSession(
        str(MODEL_DIR / onnx_file),
        providers=["CPUExecutionProvider"],
    )
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: np.array(input_vector, dtype=np.float32).reshape(1, -1)})
    return float(np.maximum(0, outputs[0].flatten()[0]))


def main() -> int:
    model_card = load_model_card()
    models = {m["model_name"]: m for m in model_card["models"]}

    print("Hash-Embedding Ablation Study")
    print("=" * 100)
    print(
        f"{'ZIP/Type':<30} {'Model':<15} {'Full':<12} {'No Embed':<12} {'Diff':<12} {'% Change':<12}"
    )
    print("-" * 100)

    for zipcode, complaint_type in TEST_COMBINATIONS:
        try:
            record = fetch_record(zipcode, complaint_type)
        except RuntimeError as exc:
            print(f"{zipcode}/{complaint_type:<25} Error: {exc}")
            continue

        full_vector = build_feature_vector(record, include_embedding=True)
        no_embed_vector = build_feature_vector(record, include_embedding=False)

        label = f"{zipcode} / {complaint_type}"

        for model_name, model_meta in models.items():
            full_pred = run_model(model_meta["onnx_file"], full_vector)
            no_embed_pred = run_model(model_meta["onnx_file"], no_embed_vector)
            diff = full_pred - no_embed_pred
            pct_change = (diff / no_embed_pred * 100) if no_embed_pred != 0 else float("inf")

            print(
                f"{label:<30} "
                f"{model_name:<15} "
                f"{full_pred:<12.2f} "
                f"{no_embed_pred:<12.2f} "
                f"{diff:<+12.2f} "
                f"{pct_change:<+12.1f}%"
            )

            label = ""  # Only print label on first row

    print("=" * 100)
    print("\nNotes:")
    print("- 'Full' uses the complete 38-dimensional feature vector.")
    print("- 'No Embed' zeros out the 32-dimensional hash embedding.")
    print("- '% Change' shows how much the prediction changes when the embedding is removed.")
    print("- A large % change means the hash embedding strongly influences that prediction.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
