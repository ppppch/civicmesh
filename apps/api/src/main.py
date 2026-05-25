from fastapi import FastAPI

from src.config.settings import get_settings
from src.routes.ask import router as ask_router
from src.routes.compute import router as compute_router
from src.routes.health import router as health_router
from src.routes.ingest import router as ingest_router

settings = get_settings()

app = FastAPI(
    title="CivicGrid NYC API",
    version="0.1.0",
    description="Local-first civic intelligence API for NYC Open Data.",
)

app.include_router(health_router)
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(compute_router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "name": "civicgrid-nyc",
        "env": settings.api_env,
        "message": "API is up. Next: ingestion, retrieval, planning, and verification routes.",
    }
