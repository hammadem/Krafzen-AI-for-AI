#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${1:-$ROOT_DIR/backups/supabase/$TIMESTAMP}"

if [[ -z "${SUPABASE_DATABASE_URL:-}" && -f "$ROOT_DIR/.env" ]]; then
  SUPABASE_DATABASE_URL="$(sed -n 's/^SUPABASE_DATABASE_URL=//p' "$ROOT_DIR/.env" | tail -n 1)"
fi

if [[ -z "${SUPABASE_DATABASE_URL:-}" ]]; then
  echo "SUPABASE_DATABASE_URL is required."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is required by the Supabase CLI. Start Docker Desktop and retry."
  exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "Creating Supabase backup in $BACKUP_DIR"
npx --yes supabase db dump --db-url "$SUPABASE_DATABASE_URL" --file "$BACKUP_DIR/roles.sql" --role-only
npx --yes supabase db dump --db-url "$SUPABASE_DATABASE_URL" --file "$BACKUP_DIR/schema.sql"
npx --yes supabase db dump --db-url "$SUPABASE_DATABASE_URL" --file "$BACKUP_DIR/data.sql" --use-copy --data-only \
  --exclude "storage.buckets_vectors" \
  --exclude "storage.vector_indexes"
npx --yes supabase db dump --db-url "$SUPABASE_DATABASE_URL" --file "$BACKUP_DIR/data.local.sql" --use-copy --data-only \
  --schema "public"

for file in roles.sql schema.sql data.sql data.local.sql; do
  test -s "$BACKUP_DIR/$file"
done

(cd "$BACKUP_DIR" && shasum -a 256 roles.sql schema.sql data.sql data.local.sql > SHA256SUMS)
cat > "$BACKUP_DIR/README.txt" <<EOF
Created: $TIMESTAMP
Source project: ${SUPABASE_PROJECT_ID:-unknown}
Files: roles.sql, schema.sql, data.sql, data.local.sql

This is a logical database backup. Supabase Storage object bytes are not included;
only their database metadata is present. data.local.sql contains only public
application data because managed service schema versions can differ locally. Keep this
directory encrypted and private.
EOF

echo "Backup completed and checksummed."
echo "$BACKUP_DIR"
