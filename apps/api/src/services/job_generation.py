from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text


CLIENT_METHODS = [
    {
        "method_id": "trend_over_time",
        "title": "Trend Over Time",
        "prompt": "How has {topic} changed over time in {geo}?",
        "requires": 2,
    },
    {
        "method_id": "geo_rank",
        "title": "Geography Ranking",
        "prompt": "Which areas have the highest {topic} burden compared with peers?",
        "requires": 2,
    },
    {
        "method_id": "before_after_window",
        "title": "Before and After Window",
        "prompt": "What changed in {topic} before vs after {event_proxy}?",
        "requires": 2,
    },
    {
        "method_id": "anomaly_screen",
        "title": "Anomaly Screen",
        "prompt": "Where are anomalous spikes in {topic} not explained by baseline volume?",
        "requires": 2,
    },
    {
        "method_id": "joinability_check",
        "title": "Joinability Check",
        "prompt": "Are these datasets reliably joinable by geography, time, or identifier?",
        "requires": 2,
    },
    {
        "method_id": "equity_gap_scan",
        "title": "Equity Gap Scan",
        "prompt": "Which geographies show the largest gap between burden and service response?",
        "requires": 3,
    },
    {
        "method_id": "resource_coverage_gap",
        "title": "Resource Coverage Gap",
        "prompt": "Where is civic need high but public resource coverage low?",
        "requires": 3,
    },
    {
        "method_id": "risk_alignment",
        "title": "Risk Alignment",
        "prompt": "Where do environmental and health risk proxies align most strongly?",
        "requires": 3,
    },
    {
        "method_id": "service_vs_outcome",
        "title": "Service vs Outcome",
        "prompt": "Do higher service actions correspond to improved outcomes by geography?",
        "requires": 3,
    },
    {
        "method_id": "co_signal_detection",
        "title": "Co-Signal Detection",
        "prompt": "Which indicators move together and where do they diverge?",
        "requires": 3,
    },
]

TOPIC_TERMS = {
    "housing": ["housing", "hpd", "building", "violation", "tenant"],
    "heat": ["heat", "hot water", "temperature", "cooling"],
    "trees": ["tree", "canopy", "greenspace", "park"],
    "schools": ["school", "education", "student"],
    "sanitation": ["sanitation", "trash", "collection", "waste"],
    "transit": ["transit", "subway", "bus", "mta"],
    "health": ["health", "hospital", "asthma", "admission"],
    "environment": ["air", "pollution", "hazard", "environment"],
    "safety": ["crime", "safety", "incident", "enforcement"],
}


@dataclass
class GeneratedJob:
    job_id: str
    title: str
    objective: str
    method_id: str
    topic: str
    dataset_ids: list[str]
    payload: dict[str, Any]


class JobGenerationService:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def generate(self, target_count: int = 10_000) -> dict[str, Any]:
        datasets = self._load_dataset_pool(limit=600)
        if len(datasets) < 10:
            raise ValueError("Insufficient ingested datasets. Run /ingest/catalog first.")

        jobs: list[GeneratedJob] = []
        seen_job_ids: set[str] = set()
        methods = CLIENT_METHODS
        topics = list(TOPIC_TERMS.keys())

        dataset_count = len(datasets)
        cursor = 0

        while len(jobs) < target_count:
            method = methods[cursor % len(methods)]
            topic = topics[(cursor // len(methods)) % len(topics)]

            ds_indices = self._pick_dataset_indices(
                seed=f"{method['method_id']}::{topic}::{cursor}",
                pool_size=dataset_count,
                required=int(method["requires"]),
            )
            chosen = [datasets[i] for i in ds_indices]
            dataset_ids = [str(d["dataset_id"]) for d in chosen]

            title = f"{method['title']}: {topic.title()} #{len(jobs) + 1}"
            objective = method["prompt"].format(topic=topic, geo="NYC geographies", event_proxy="policy/event windows")
            job_id = _stable_job_id(
                method_id=str(method["method_id"]),
                topic=topic,
                dataset_ids=dataset_ids,
                ordinal=cursor,
            )
            if job_id in seen_job_ids:
                cursor += 1
                continue

            payload = {
                "method": method,
                "topic": topic,
                "datasets": [
                    {
                        "dataset_id": str(d["dataset_id"]),
                        "title": str(d["title"]),
                        "category": str(d["category"]),
                        "source_url": str(d["source_url"]),
                    }
                    for d in chosen
                ],
                "client_plan": [
                    "Load selected dataset metadata and schema hints",
                    "Run local embedding/rerank for field alignment",
                    "Execute deterministic aggregation recipe",
                    "Attach reproducibility payload and verification checks",
                ],
                "verification_checks": [
                    "schema_joinability",
                    "geography_field_presence",
                    "time_field_presence",
                    "replica_consensus_required",
                ],
            }

            jobs.append(
                GeneratedJob(
                    job_id=job_id,
                    title=title,
                    objective=objective,
                    method_id=str(method["method_id"]),
                    topic=topic,
                    dataset_ids=dataset_ids,
                    payload=payload,
                )
            )
            seen_job_ids.add(job_id)
            cursor += 1

        self._persist_jobs(jobs)
        return {
            "target_count": target_count,
            "generated_count": len(jobs),
            "dataset_pool_size": len(datasets),
            "methods": len(methods),
            "topics": len(topics),
        }

    def list_generated_jobs(self, offset: int = 0, limit: int = 50, topic: str | None = None) -> dict[str, Any]:
        where_clause = ""
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if topic:
            where_clause = "WHERE topic = :topic"
            params["topic"] = topic

        query = text(
            f"""
            SELECT job_id, title, objective, method_id, topic, dataset_ids, payload, created_on_ts
            FROM generated_jobs
            {where_clause}
            ORDER BY created_on_ts DESC, job_id
            OFFSET :offset
            LIMIT :limit
            """
        )

        count_query = text(
            f"""
            SELECT COUNT(*) AS total
            FROM generated_jobs
            {where_clause}
            """
        )

        with self.engine.begin() as conn:
            rows = conn.execute(query, params).mappings().all()
            total = conn.execute(count_query, params).mappings().first()

        return {
            "total": int(total["total"]) if total else 0,
            "offset": offset,
            "limit": limit,
            "items": [
                {
                    "job_id": r["job_id"],
                    "title": r["title"],
                    "objective": r["objective"],
                    "method_id": r["method_id"],
                    "topic": r["topic"],
                    "dataset_ids": r["dataset_ids"],
                    "payload": r["payload"],
                    "created_on_ts": r["created_on_ts"].isoformat() if r["created_on_ts"] else None,
                }
                for r in rows
            ],
        }

    def get_generated_job(self, job_id: str) -> dict[str, Any] | None:
        query = text(
            """
            SELECT job_id, title, objective, method_id, topic, dataset_ids, payload, created_on_ts
            FROM generated_jobs
            WHERE job_id = :job_id
            """
        )

        with self.engine.begin() as conn:
            row = conn.execute(query, {"job_id": job_id}).mappings().first()

        if row is None:
            return None

        return {
            "job_id": row["job_id"],
            "title": row["title"],
            "objective": row["objective"],
            "method_id": row["method_id"],
            "topic": row["topic"],
            "dataset_ids": row["dataset_ids"],
            "payload": row["payload"],
            "created_on_ts": row["created_on_ts"].isoformat() if row["created_on_ts"] else None,
        }

    def _load_dataset_pool(self, limit: int) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT dataset_id, title, category, source_url
            FROM datasets_metadata
            WHERE source_url IS NOT NULL
            ORDER BY updated_on_ts DESC
            LIMIT :limit
            """
        )
        with self.engine.begin() as conn:
            rows = conn.execute(query, {"limit": limit}).mappings().all()
        return [dict(r) for r in rows]

    def _persist_jobs(self, jobs: list[GeneratedJob]) -> None:
        statement = text(
            """
            INSERT INTO generated_jobs (job_id, title, objective, method_id, topic, dataset_ids, payload, created_on_ts)
            VALUES (:job_id, :title, :objective, :method_id, :topic, :dataset_ids, CAST(:payload AS JSONB), NOW())
            ON CONFLICT (job_id) DO UPDATE SET
              title = EXCLUDED.title,
              objective = EXCLUDED.objective,
              method_id = EXCLUDED.method_id,
              topic = EXCLUDED.topic,
              dataset_ids = EXCLUDED.dataset_ids,
              payload = EXCLUDED.payload,
              created_on_ts = NOW();
            """
        )

        values = [
            {
                "job_id": j.job_id,
                "title": j.title,
                "objective": j.objective,
                "method_id": j.method_id,
                "topic": j.topic,
                "dataset_ids": j.dataset_ids,
                "payload": json.dumps(j.payload),
            }
            for j in jobs
        ]

        with self.engine.begin() as conn:
            conn.execute(statement, values)

    def _pick_dataset_indices(self, seed: str, pool_size: int, required: int) -> list[int]:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        indices: list[int] = []
        i = 0
        while len(indices) < required:
            value = int.from_bytes(digest[i % len(digest): (i % len(digest)) + 2], "big", signed=False)
            idx = value % pool_size
            if idx not in indices:
                indices.append(idx)
            i += 1
        return indices


def _stable_job_id(method_id: str, topic: str, dataset_ids: list[str], ordinal: int) -> str:
    source = f"{method_id}:{topic}:{ordinal}:{'|'.join(sorted(dataset_ids))}"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"gen-{method_id}-{topic}-{digest}"
