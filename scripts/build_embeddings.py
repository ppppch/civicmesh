#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    api_path = root / "apps" / "api"
    sys.path.insert(0, str(api_path))

    from src.config.settings import get_settings
    from src.services.preembed import build_preembedding_artifacts

    parser = argparse.ArgumentParser(description="Build CivicGrid pre-embedding artifacts")
    parser.add_argument("--max-datasets", type=int, default=60)
    args = parser.parse_args()

    s = get_settings()
    summary = build_preembedding_artifacts(
        host=s.postgres_host,
        port=s.postgres_port,
        db=s.postgres_db,
        user=s.postgres_user,
        password=s.postgres_password,
        output_dir=s.embedding_artifacts_dir,
        max_datasets=args.max_datasets,
        model_name=s.embedding_model_name,
    )

    print(
        f"run_id={summary.run_id} model={summary.model_name} "
        f"chunks={summary.chunks} shards={summary.shards} manifest={summary.manifest_path}"
    )


if __name__ == "__main__":
    main()
