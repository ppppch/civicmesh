from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.services.auth import resolve_identity
from src.services.catalog import build_database_url
from src.services.publish_runs import PublishRunInput, PublishRunService

router = APIRouter(prefix="/runs", tags=["runs"])


class PublishRunRequest(BaseModel):
    run_id: str = Field(min_length=6, max_length=120)
    question: str = Field(min_length=5, max_length=600)
    model_name: str = Field(min_length=2, max_length=200)
    embedding_key: str = Field(min_length=8, max_length=200)
    selected_dataset_ids: list[str] = Field(min_length=1)
    result_payload: dict


def _build_service() -> PublishRunService:
    s = get_settings()
    return PublishRunService(
        database_url=build_database_url(
            host=s.postgres_host,
            port=s.postgres_port,
            db=s.postgres_db,
            user=s.postgres_user,
            password=s.postgres_password,
        )
    )


@router.post("/publish", summary="Publish a client-computed run")
def publish_run(payload: PublishRunRequest, authorization: str | None = Header(default=None)) -> dict:
    s = get_settings()
    service = _build_service()

    try:
        identity = resolve_identity(auth_mode=s.auth_mode, authorization_header=authorization)
        result = service.publish(
            user_id=identity.user_id,
            data=PublishRunInput(
                run_id=payload.run_id,
                question=payload.question,
                model_name=payload.model_name,
                embedding_key=payload.embedding_key,
                selected_dataset_ids=payload.selected_dataset_ids,
                result_payload=payload.result_payload,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "run_id": result.run_id,
        "user_id": result.user_id,
        "created": result.created,
        "created_on_ts": result.created_on_ts,
    }


@router.get("/mine", summary="List my published runs")
def list_my_runs(
    authorization: str | None = Header(default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    s = get_settings()
    service = _build_service()

    try:
        identity = resolve_identity(auth_mode=s.auth_mode, authorization_header=authorization)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "user_id": identity.user_id,
        "items": service.list_for_user(user_id=identity.user_id, limit=limit),
    }
