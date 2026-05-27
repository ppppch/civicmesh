from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text


@dataclass
class PublishRunInput:
    run_id: str
    question: str
    model_name: str
    embedding_key: str
    selected_dataset_ids: list[str]
    result_payload: dict[str, Any]


@dataclass
class PublishRunResult:
    run_id: str
    user_id: str
    created: bool
    created_on_ts: str | None


class PublishRunService:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def publish(self, user_id: str, data: PublishRunInput) -> PublishRunResult:
        _validate_payload(data)
        idem_key = _idempotency_key(user_id=user_id, run_id=data.run_id, payload=data.result_payload)

        upsert_sql = text(
            """
            INSERT INTO published_runs (
              run_id,
              user_id,
              question,
              model_name,
              embedding_key,
              selected_dataset_ids,
              result_payload,
              idempotency_key,
              created_on_ts
            ) VALUES (
              :run_id,
              :user_id,
              :question,
              :model_name,
              :embedding_key,
              :selected_dataset_ids,
              CAST(:result_payload AS JSONB),
              :idempotency_key,
              NOW()
            )
            ON CONFLICT (run_id) DO UPDATE SET
              question = EXCLUDED.question,
              model_name = EXCLUDED.model_name,
              embedding_key = EXCLUDED.embedding_key,
              selected_dataset_ids = EXCLUDED.selected_dataset_ids,
              result_payload = EXCLUDED.result_payload,
              idempotency_key = EXCLUDED.idempotency_key
            RETURNING created_on_ts;
            """
        )

        with self.engine.begin() as conn:
            row = conn.execute(
                upsert_sql,
                {
                    "run_id": data.run_id,
                    "user_id": user_id,
                    "question": data.question,
                    "model_name": data.model_name,
                    "embedding_key": data.embedding_key,
                    "selected_dataset_ids": data.selected_dataset_ids,
                    "result_payload": json.dumps(data.result_payload),
                    "idempotency_key": idem_key,
                },
            ).mappings().first()

        return PublishRunResult(
            run_id=data.run_id,
            user_id=user_id,
            created=True,
            created_on_ts=row["created_on_ts"].isoformat() if row and row["created_on_ts"] else None,
        )

    def list_for_user(self, user_id: str, limit: int = 25) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT run_id, question, model_name, embedding_key, selected_dataset_ids, result_payload, created_on_ts
            FROM published_runs
            WHERE user_id = :user_id
            ORDER BY created_on_ts DESC
            LIMIT :limit
            """
        )

        with self.engine.begin() as conn:
            rows = conn.execute(sql, {"user_id": user_id, "limit": limit}).mappings().all()

        return [
            {
                "run_id": r["run_id"],
                "question": r["question"],
                "model_name": r["model_name"],
                "embedding_key": r["embedding_key"],
                "selected_dataset_ids": r["selected_dataset_ids"],
                "result_payload": r["result_payload"],
                "created_on_ts": r["created_on_ts"].isoformat() if r["created_on_ts"] else None,
            }
            for r in rows
        ]


def _validate_payload(data: PublishRunInput) -> None:
    if not data.run_id.strip():
        raise ValueError("run_id is required")
    if len(data.question.strip()) < 5:
        raise ValueError("question is too short")
    if not data.model_name.strip():
        raise ValueError("model_name is required")
    if not data.embedding_key.strip():
        raise ValueError("embedding_key is required")
    if not data.selected_dataset_ids:
        raise ValueError("selected_dataset_ids cannot be empty")


def _idempotency_key(*, user_id: str, run_id: str, payload: dict[str, Any]) -> str:
    serial = json.dumps(payload, sort_keys=True)
    src = f"{user_id}:{run_id}:{serial}".encode("utf-8")
    return hashlib.sha256(src).hexdigest()
