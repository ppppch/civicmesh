from fastapi import APIRouter, Query

from src.config.settings import get_settings
from src.services.preembed import PreembedBuilder
from src.services.catalog import build_database_url

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/build", summary="Build pre-embedding artifacts from ingested catalog")
def build_embeddings(max_datasets: int = Query(default=60, ge=20, le=500)) -> dict[str, object]:
    s = get_settings()
    summary = PreembedBuilder(
        database_url=build_database_url(
            host=s.postgres_host,
            port=s.postgres_port,
            db=s.postgres_db,
            user=s.postgres_user,
            password=s.postgres_password,
        ),
        output_dir=s.embedding_artifacts_dir,
        model_name=s.embedding_model_name,
    ).build(max_datasets=max_datasets)

    return {
        "run_id": summary.run_id,
        "model_name": summary.model_name,
        "chunks": summary.chunks,
        "shards": summary.shards,
        "manifest_path": summary.manifest_path,
    }
