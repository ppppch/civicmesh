#!/usr/bin/env zsh
set -euo pipefail

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=civicgrid}"
: "${POSTGRES_USER:=civicgrid}"
: "${POSTGRES_PASSWORD:=civicgrid}"

export PGPASSWORD="$POSTGRES_PASSWORD"

for migration in db/migrations/*.sql; do
  echo "Applying $migration"
  psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -v ON_ERROR_STOP=1 \
    -f "$migration"
done

echo "Migrations applied successfully."
