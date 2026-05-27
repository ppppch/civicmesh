CREATE TABLE IF NOT EXISTS generated_jobs (
  id BIGSERIAL PRIMARY KEY,
  job_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  objective TEXT NOT NULL,
  method_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  dataset_ids TEXT[] NOT NULL,
  payload JSONB NOT NULL,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_jobs_topic ON generated_jobs (topic);
CREATE INDEX IF NOT EXISTS idx_generated_jobs_method_id ON generated_jobs (method_id);
CREATE INDEX IF NOT EXISTS idx_generated_jobs_created_on_ts ON generated_jobs (created_on_ts DESC);
