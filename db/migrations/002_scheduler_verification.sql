-- Deterministic work-unit and verification baseline
CREATE TABLE IF NOT EXISTS work_units (
  id BIGSERIAL PRIMARY KEY,
  job_id TEXT NOT NULL,
  task_type TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  payload JSONB NOT NULL,
  model_name TEXT,
  model_version TEXT,
  max_runtime_seconds INTEGER NOT NULL,
  replica_factor INTEGER NOT NULL DEFAULT 3,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS work_unit_results (
  id BIGSERIAL PRIMARY KEY,
  work_unit_id BIGINT NOT NULL REFERENCES work_units(id) ON DELETE CASCADE,
  worker_id TEXT NOT NULL,
  output_hash TEXT NOT NULL,
  output_payload JSONB NOT NULL,
  runtime_ms INTEGER,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS work_unit_consensus (
  work_unit_id BIGINT PRIMARY KEY REFERENCES work_units(id) ON DELETE CASCADE,
  consensus_status TEXT NOT NULL,
  agreement_ratio NUMERIC(5,4),
  confidence_score NUMERIC(5,4),
  decided_on_ts TIMESTAMPTZ
);
