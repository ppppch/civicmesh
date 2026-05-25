-- Dataset metadata catalog (MVP baseline)
CREATE TABLE IF NOT EXISTS datasets_metadata (
  dataset_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  agency_name TEXT,
  category TEXT,
  tags JSONB,
  rows_count BIGINT,
  columns_count INTEGER,
  source_url TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  last_ingest_run_id TEXT,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_datasets_category ON datasets_metadata (category);
CREATE INDEX IF NOT EXISTS idx_datasets_agency_name ON datasets_metadata (agency_name);
CREATE INDEX IF NOT EXISTS idx_datasets_tsv ON datasets_metadata
USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(category, '')));
