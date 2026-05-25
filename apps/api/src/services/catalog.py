from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.services.socrata import SocrataClient, SocrataDataset


@dataclass
class IngestRunSummary:
    ingest_run_id: str
    datasets_scanned: int
    datasets_selected: int
    status: str


class CatalogService:
    def __init__(self, *, domain: str, app_token: str | None, database_url: str) -> None:
        self.client = SocrataClient(domain=domain, app_token=app_token)
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def ingest_catalog(self, limit: int = 200, top_k: int = 100) -> IngestRunSummary:
        datasets = self.client.fetch_catalog(limit=limit)
        scored = sorted(datasets, key=_score_dataset, reverse=True)
        selected = scored[:top_k]
        ingest_run_id = str(uuid.uuid4())

        if selected:
            self._upsert(selected, ingest_run_id=ingest_run_id)

        return IngestRunSummary(
            ingest_run_id=ingest_run_id,
            datasets_scanned=len(datasets),
            datasets_selected=len(selected),
            status="completed",
        )

    def search(self, query: str, limit: int = 10) -> list[dict[str, str | int]]:
        if not query.strip():
            return []

        sql = text(
            """
            SELECT
              dataset_id,
              title,
              COALESCE(description, '') AS description,
              COALESCE(agency_name, 'Unknown') AS agency_name,
              COALESCE(category, 'Other') AS category,
              rows_count,
              source_url,
              ts_rank(
                to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(category, '')),
                websearch_to_tsquery('english', :q)
              ) AS rank
            FROM datasets_metadata
            WHERE to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(category, ''))
              @@ websearch_to_tsquery('english', :q)
            ORDER BY rank DESC, updated_on_ts DESC
            LIMIT :limit
            """
        )

        with self.engine.begin() as conn:
            rows = conn.execute(sql, {"q": query, "limit": limit}).mappings().all()

        return [
            {
                "dataset_id": row["dataset_id"],
                "title": row["title"],
                "description": row["description"][:280],
                "agency_name": row["agency_name"],
                "category": row["category"],
                "rows_count": int(row["rows_count"] or 0),
                "source_url": row["source_url"],
            }
            for row in rows
        ]

    def _upsert(self, datasets: list[SocrataDataset], ingest_run_id: str) -> None:
        sql = text(
            """
            INSERT INTO datasets_metadata (
              dataset_id,
              title,
              description,
              agency_name,
              category,
              tags,
              rows_count,
              columns_count,
              source_url,
              created_at,
              updated_at,
              last_ingest_run_id,
              updated_on_ts
            ) VALUES (
              :dataset_id,
              :title,
              :description,
              :agency_name,
              :category,
              CAST(:tags AS JSONB),
              :rows_count,
              :columns_count,
              :source_url,
              :created_at,
              :updated_at,
              :last_ingest_run_id,
              NOW()
            )
            ON CONFLICT (dataset_id) DO UPDATE SET
              title = EXCLUDED.title,
              description = EXCLUDED.description,
              agency_name = EXCLUDED.agency_name,
              category = EXCLUDED.category,
              tags = EXCLUDED.tags,
              rows_count = EXCLUDED.rows_count,
              columns_count = EXCLUDED.columns_count,
              source_url = EXCLUDED.source_url,
              created_at = EXCLUDED.created_at,
              updated_at = EXCLUDED.updated_at,
              last_ingest_run_id = EXCLUDED.last_ingest_run_id,
              updated_on_ts = NOW();
            """
        )

        payload = [
            {
                "dataset_id": ds.dataset_id,
                "title": ds.title,
                "description": ds.description,
                "agency_name": ds.agency_name,
                "category": ds.category,
                "tags": json.dumps(ds.tags),
                "rows_count": ds.rows_count,
                "columns_count": ds.columns_count,
                "source_url": ds.source_url,
                "created_at": ds.created_at,
                "updated_at": ds.updated_at,
                "last_ingest_run_id": ingest_run_id,
            }
            for ds in datasets
        ]

        with self.engine.begin() as conn:
            conn.execute(sql, payload)


def _score_dataset(dataset: SocrataDataset) -> float:
    score = 0.0

    if dataset.description:
        score += 2.0
    if dataset.tags:
        score += 1.5

    if 500 <= dataset.rows_count <= 3_000_000:
        score += 2.0
    elif dataset.rows_count > 0:
        score += 1.0

    if 5 <= dataset.columns_count <= 80:
        score += 1.5

    text_blob = f"{dataset.title} {dataset.description} {' '.join(dataset.tags)}".lower()
    civic_terms = [
        "311",
        "housing",
        "heat",
        "tree",
        "school",
        "transit",
        "health",
        "violation",
        "sanitation",
        "safety",
    ]
    score += sum(0.4 for t in civic_terms if t in text_blob)

    now = datetime.now(tz=UTC)
    updated_at = dataset.updated_at
    if updated_at is not None:
        age_days = max((now - updated_at).days, 0)
        if age_days <= 30:
            score += 2.0
        elif age_days <= 180:
            score += 1.0
        elif age_days <= 365:
            score += 0.5

    return score


def build_database_url(*, host: str, port: int, db: str, user: str, password: str) -> str:
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
