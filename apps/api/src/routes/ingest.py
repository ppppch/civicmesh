from fastapi import APIRouter, Query

from src.services.ingest_stub import run_catalog_selection

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/catalog", summary="Run catalog selection stub")
def ingest_catalog(limit: int = Query(default=200, ge=25, le=1000)) -> dict[str, int | str]:
    result = run_catalog_selection(limit=limit)
    return {
        "datasets_scanned": result.datasets_scanned,
        "datasets_selected": result.datasets_selected,
        "status": result.status,
    }
