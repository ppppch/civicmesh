from fastapi import APIRouter

from src.config.settings import get_settings

router = APIRouter(prefix="/compute", tags=["compute"])


@router.get("/status", summary="Local worker simulation status")
def compute_status() -> dict[str, int | float]:
    s = get_settings()
    return {
        "worker_count": s.sim_worker_count,
        "replica_factor": s.sim_replica_factor,
        "gold_task_ratio": s.sim_gold_task_ratio,
        "max_runtime_seconds": s.sim_max_runtime_seconds,
    }
