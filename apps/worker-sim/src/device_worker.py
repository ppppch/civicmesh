from dataclasses import dataclass


@dataclass
class SimulatedTask:
    task_id: str
    task_type: str
    max_runtime_seconds: int


def execute_task(task: SimulatedTask) -> dict[str, str | int]:
    # Safe bounded placeholder executor for local simulation.
    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "result": "ok",
        "runtime_ms": min(task.max_runtime_seconds * 100, 1000),
    }
