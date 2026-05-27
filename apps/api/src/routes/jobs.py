from fastapi import APIRouter, HTTPException, Query

from src.config.settings import get_settings
from src.services.catalog import build_database_url
from src.services.job_generation import JobGenerationService
from src.services.job_runner import JobRunner
from src.services.soql import SoqlClient

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _build_runner() -> JobRunner:
    s = get_settings()
    return JobRunner(
        database_url=build_database_url(
            host=s.postgres_host,
            port=s.postgres_port,
            db=s.postgres_db,
            user=s.postgres_user,
            password=s.postgres_password,
        ),
        soql_client=SoqlClient(domain=s.socrata_domain, app_token=s.socrata_app_token),
    )


def _build_generation_service() -> JobGenerationService:
    s = get_settings()
    return JobGenerationService(
        database_url=build_database_url(
            host=s.postgres_host,
            port=s.postgres_port,
            db=s.postgres_db,
            user=s.postgres_user,
            password=s.postgres_password,
        )
    )


@router.get("", summary="List available NYC data-science jobs")
def list_jobs() -> dict[str, object]:
    runner = _build_runner()
    jobs = runner.list_jobs()
    return {
        "jobs": [
            {
                "job_id": j.job_id,
                "title": j.title,
                "objective": j.objective,
                "required_roles": j.required_roles,
                "output_fields": j.output_fields,
            }
            for j in jobs
        ]
    }


@router.post("/{job_id}/run", summary="Run deterministic NYC data-science job")
def run_job(job_id: str, limit: int = Query(default=10, ge=3, le=25)) -> dict[str, object]:
    runner = _build_runner()
    try:
        result = runner.run_job(job_id=job_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "job_id": result.job_id,
        "title": result.title,
        "objective": result.objective,
        "datasets": [
            {
                "role": d.role,
                "dataset_id": d.dataset_id,
                "title": d.title,
                "source_url": d.source_url,
            }
            for d in result.datasets
        ],
        "rows": result.output_rows,
        "reproducibility": result.reproducibility,
        "caveats": result.caveats,
    }


@router.post("/generated/build", summary="Generate large systematic job catalog from ingested NYC datasets")
def build_generated_jobs(target_count: int = Query(default=10000, ge=100, le=50000)) -> dict[str, object]:
    service = _build_generation_service()
    try:
        return service.generate(target_count=target_count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/generated", summary="List generated data-science jobs")
def list_generated_jobs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    topic: str | None = Query(default=None),
) -> dict[str, object]:
    service = _build_generation_service()
    return service.list_generated_jobs(offset=offset, limit=limit, topic=topic)


@router.get("/generated/{job_id}", summary="Get one generated job")
def get_generated_job(job_id: str) -> dict[str, object]:
    service = _build_generation_service()
    item = service.get_generated_job(job_id=job_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Generated job not found: {job_id}")
    return item
