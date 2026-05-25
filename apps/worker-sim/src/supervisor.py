from dataclasses import dataclass

from src.device_worker import SimulatedTask, execute_task


@dataclass
class WorkerConfig:
    worker_count: int = 8
    replica_factor: int = 3


def main() -> None:
    cfg = WorkerConfig()
    sample_task = SimulatedTask(
        task_id="demo-task-0001",
        task_type="dataset_rerank",
        max_runtime_seconds=20,
    )
    result = execute_task(sample_task)

    print(
        "worker-sim bootstrap",
        f"workers={cfg.worker_count}",
        f"replicas={cfg.replica_factor}",
        f"sample_result={result['result']}",
    )


if __name__ == "__main__":
    main()
