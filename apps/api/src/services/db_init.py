from sqlalchemy import create_engine, text


def ensure_catalog_extensions(database_url: str) -> None:
    engine = create_engine(database_url, pool_pre_ping=True)
    sql = text("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    with engine.begin() as conn:
        conn.execute(sql)
