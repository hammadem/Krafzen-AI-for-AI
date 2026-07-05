#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${1:-}"
LOCAL_DB_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"

if [[ -z "$BACKUP_DIR" ]]; then
  echo "Usage: $0 backups/supabase/<timestamp>"
  exit 1
fi

BACKUP_DIR="$(cd "$BACKUP_DIR" && pwd)"
for file in roles.sql schema.sql data.sql; do
  if [[ ! -s "$BACKUP_DIR/$file" ]]; then
    echo "Missing or empty backup file: $BACKUP_DIR/$file"
    exit 1
  fi
done
DATA_FILE="$BACKUP_DIR/data.sql"
if [[ -s "$BACKUP_DIR/data.local.sql" ]]; then
  DATA_FILE="$BACKUP_DIR/data.local.sql"
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required to restore the backup."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is required for local Supabase. Start Docker Desktop and retry."
  exit 1
fi

if [[ -f "$BACKUP_DIR/SHA256SUMS" ]]; then
  (cd "$BACKUP_DIR" && shasum -a 256 -c SHA256SUMS)
fi

echo "This deletes and recreates the LOCAL Supabase database on port 54322."
read -r -p "Type RESTORE LOCAL to continue: " confirmation
if [[ "$confirmation" != "RESTORE LOCAL" ]]; then
  echo "Restore cancelled."
  exit 1
fi

cd "$ROOT_DIR"
MIGRATIONS_DIR="$ROOT_DIR/supabase/migrations"
MIGRATIONS_HOLD="$ROOT_DIR/supabase/migrations.restore-hold"

restore_migrations() {
  if [[ -d "$MIGRATIONS_HOLD" ]]; then
    mv "$MIGRATIONS_HOLD" "$MIGRATIONS_DIR"
  fi
}
trap restore_migrations EXIT

npx --yes supabase stop --no-backup >/dev/null 2>&1 || true
if [[ -d "$MIGRATIONS_DIR" ]]; then
  mv "$MIGRATIONS_DIR" "$MIGRATIONS_HOLD"
fi
npx --yes supabase start
restore_migrations
trap - EXIT

psql \
  --single-transaction \
  --variable ON_ERROR_STOP=1 \
  --file "$BACKUP_DIR/roles.sql" \
  --file "$BACKUP_DIR/schema.sql" \
  --command "SET session_replication_role = replica" \
  --file "$DATA_FILE" \
  --dbname "$LOCAL_DB_URL"

psql "$LOCAL_DB_URL" --variable ON_ERROR_STOP=1 --command \
  "SELECT schemaname, count(*) AS tables FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') GROUP BY schemaname ORDER BY schemaname;"

echo "Local restore completed. Run 'npx supabase status' for local API credentials."
