from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import create_engine, text

from src.services.catalog import build_database_url

try:
    from fastembed import TextEmbedding
except ImportError:
    TextEmbedding = None


@dataclass
class EmbeddingBuildSummary:
    run_id: str
    model_name: str
    chunks: int
    shards: int
    manifest_path: str


class PreembedBuilder:
    def __init__(
        self,
        *,
        database_url: str,
        output_dir: str,
        model_name: str = "hash-embed-v1",
        shard_count: int = 6,
    ) -> None:
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.shard_count = shard_count

    def build(self, max_datasets: int = 60) -> EmbeddingBuildSummary:
        run_id = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
        rows = self._load_datasets(limit=max_datasets)
        chunks = self._make_chunks(rows)

        shard_files = self._write_shards(run_id=run_id, chunks=chunks)
        manifest_path = self._write_manifest(run_id=run_id, chunks=chunks, shard_files=shard_files)

        return EmbeddingBuildSummary(
            run_id=run_id,
            model_name=self.model_name,
            chunks=len(chunks),
            shards=len(shard_files),
            manifest_path=str(manifest_path),
        )

    def _load_datasets(self, limit: int) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT dataset_id, title, COALESCE(description, '') AS description,
                   COALESCE(category, 'Other') AS category,
                   COALESCE(agency_name, 'Unknown') AS agency_name
            FROM datasets_metadata
            ORDER BY updated_on_ts DESC
            LIMIT :limit
            """
        )

        with self.engine.begin() as conn:
            rows = conn.execute(sql, {"limit": limit}).mappings().all()

        return [dict(r) for r in rows]

    def _make_chunks(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        texts_to_embed: list[str] = []
        pending_meta: list[tuple[str, str, str]] = []
        for row in rows:
            dataset_id = str(row["dataset_id"])
            title = str(row["title"])
            description = str(row["description"])
            category = str(row["category"])
            agency = str(row["agency_name"])

            texts = [
                ("metadata-title", title),
                ("metadata-full", f"{title}\n{description}\nCategory: {category}\nAgency: {agency}"),
            ]

            for chunk_type, text_value in texts:
                pending_meta.append((dataset_id, chunk_type, text_value))
                texts_to_embed.append(text_value)

        vectors, used_model = _embed_texts(texts_to_embed, model_name=self.model_name)
        self.model_name = used_model

        for i, (dataset_id, chunk_type, text_value) in enumerate(pending_meta):
            chunks.append(
                {
                    "chunk_id": f"{dataset_id}::{chunk_type}",
                    "dataset_id": dataset_id,
                    "chunk_type": chunk_type,
                    "text": text_value,
                    "vector": vectors[i],
                }
            )

        return chunks

    def _write_shards(self, run_id: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        buckets: list[list[dict[str, Any]]] = [[] for _ in range(self.shard_count)]
        for chunk in chunks:
            index = int(hashlib.sha256(chunk["dataset_id"].encode("utf-8")).hexdigest(), 16) % self.shard_count
            buckets[index].append(chunk)

        shard_files: list[dict[str, Any]] = []
        for idx, shard_chunks in enumerate(buckets):
            filename = self.output_dir / f"embeddings_{run_id}_shard_{idx}.jsonl.gz"
            with gzip.open(filename, "wt", encoding="utf-8") as fh:
                for row in shard_chunks:
                    fh.write(json.dumps(row) + "\n")

            checksum = _sha256_file(filename)
            shard_files.append(
                {
                    "shard_index": idx,
                    "path": str(filename),
                    "rows": len(shard_chunks),
                    "sha256": checksum,
                }
            )

        return shard_files

    def _write_manifest(
        self,
        *,
        run_id: str,
        chunks: list[dict[str, Any]],
        shard_files: list[dict[str, Any]],
    ) -> Path:
        manifest = {
            "run_id": run_id,
            "created_at": datetime.now(tz=UTC).isoformat(),
            "model_name": self.model_name,
            "vector_dim": 384,
            "chunk_count": len(chunks),
            "shard_count": len(shard_files),
            "shards": shard_files,
        }

        path = self.output_dir / f"manifest_{run_id}.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path


def _embed_text_hash(text_value: str, dim: int = 384) -> list[float]:
    # Deterministic local baseline embedding. Replace with model-based embedding in next step.
    digest = hashlib.sha256(text_value.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big", signed=False)
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=dim).astype(np.float32)
    norm = float(np.linalg.norm(vec))
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()


def _embed_texts(texts: list[str], model_name: str) -> tuple[list[list[float]], str]:
    if not texts:
        return [], model_name

    if TextEmbedding is not None:
        try:
            model = TextEmbedding(model_name=model_name)
            vectors = [np.asarray(v, dtype=np.float32) for v in model.embed(texts)]
            normalized: list[list[float]] = []
            for vec in vectors:
                norm = float(np.linalg.norm(vec))
                normalized.append((vec / norm).tolist() if norm > 0 else vec.tolist())
            return normalized, model_name
        except Exception:
            # Fall through to deterministic backup embedding.
            pass

    return [_embed_text_hash(t) for t in texts], "hash-embed-v1"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_preembedding_artifacts(
    *,
    host: str,
    port: int,
    db: str,
    user: str,
    password: str,
    output_dir: str,
    max_datasets: int,
    model_name: str = "BAAI/bge-small-en-v1.5",
) -> EmbeddingBuildSummary:
    builder = PreembedBuilder(
        database_url=build_database_url(host=host, port=port, db=db, user=user, password=password),
        output_dir=output_dir,
        model_name=model_name,
    )
    return builder.build(max_datasets=max_datasets)
