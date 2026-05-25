from fastapi import APIRouter, Query

from src.config.settings import get_settings
from src.services.catalog import CatalogService, build_database_url

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/search", summary="Search ingested datasets")
def search_datasets(query: str = Query(min_length=2), limit: int = Query(default=10, ge=1, le=25)) -> dict[str, object]:
    s = get_settings()
    service = CatalogService(
        domain=s.socrata_domain,
        app_token=s.socrata_app_token,
        database_url=build_database_url(
            host=s.postgres_host,
            port=s.postgres_port,
            db=s.postgres_db,
            user=s.postgres_user,
            password=s.postgres_password,
        ),
    )

    return {
        "query": query,
        "results": service.search(query=query, limit=limit),
    }
