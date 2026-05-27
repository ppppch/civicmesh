CREATE TABLE IF NOT EXISTS published_runs (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL UNIQUE,
  user_id TEXT NOT NULL,
  question TEXT NOT NULL,
  model_name TEXT NOT NULL,
  embedding_key TEXT NOT NULL,
  selected_dataset_ids TEXT[] NOT NULL,
  result_payload JSONB NOT NULL,
  idempotency_key TEXT NOT NULL,
  created_on_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_published_runs_idempotency_key
  ON published_runs (idempotency_key);
CREATE INDEX IF NOT EXISTS idx_published_runs_user_id_created
  ON published_runs (user_id, created_on_ts DESC);
