from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_env: str = "local"
    api_log_level: str = "info"
    auth_mode: str = "dev"
    cors_allow_origins: str = "http://localhost:5173"

    socrata_domain: str = "data.cityofnewyork.us"
    socrata_app_token: str | None = None
    embedding_artifacts_dir: str = "data/artifacts/embeddings"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "civicgrid"
    postgres_user: str = "civicgrid"
    postgres_password: str = "civicgrid"

    redis_host: str = "localhost"
    redis_port: int = 6379

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = "dev-qdrant-key"

    sim_worker_count: int = 8
    sim_max_runtime_seconds: int = 20
    sim_replica_factor: int = 3
    sim_gold_task_ratio: float = 0.15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
