-- Job run and embedding build manifests for reproducibility
CREATE TABLE IF NOT EXISTS job_run_artifacts (
  id BIGSERIAL PRIMARY KEY,
  job_id TEXT NOT NULL,
  run_token TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_job_run_token ON job_run_artifacts (run_token);
CREATE INDEX IF NOT EXISTS idx_job_run_job_id ON job_run_artifacts (job_id);

CREATE TABLE IF NOT EXISTS embedding_build_manifests (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL,
  model_name TEXT NOT NULL,
  manifest_payload JSONB NOT NULL,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_embedding_build_run_id ON embedding_build_manifests (run_id);
