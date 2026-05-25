from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness check")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version", summary="Version info")
def version() -> dict[str, str]:
    return {"service": "civicmesh-api", "version": "0.1.0"}
