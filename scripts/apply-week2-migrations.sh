#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_URL="${SUPABASE_DATABASE_URL:-}"

if [[ -z "$DATABASE_URL" && -f "$ROOT_DIR/.env" ]]; then
  DATABASE_URL="$(sed -n 's/^SUPABASE_DATABASE_URL=//p' "$ROOT_DIR/.env" | tail -n 1)"
fi

if [[ -z "$DATABASE_URL" ]]; then
  echo "SUPABASE_DATABASE_URL is required."
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required."
  exit 1
fi

echo "This applies Week 2 migrations 002 through 012, followed by the RLS migration."
echo "Confirm that a current database backup exists before continuing."
read -r -p "Type APPLY WEEK2 to continue: " confirmation
if [[ "$confirmation" != "APPLY WEEK2" ]]; then
  echo "Migration cancelled."
  exit 1
fi

for migration in \
  002_week1_architecture_foundations.sql \
  003_workspace_tables.sql \
  004_week2_activity_notifications.sql \
  005_add_name_to_files.sql \
  006_exports.sql \
  007_workspace_invites.sql \
  008_align_job_status_to_contract.sql \
  009_add_project_id_to_chat_sessions.sql \
  010_activity_events_audit_contract.sql \
  011_file_activity_lifecycle.sql \
  012_file_revision_approval.sql
do
  echo "Applying $migration"
  psql "$DATABASE_URL" \
    --set ON_ERROR_STOP=1 \
    --file "$ROOT_DIR/backend/app/db/migrations/$migration"
done

echo "Applying RLS enforcement"
psql "$DATABASE_URL" \
  --set ON_ERROR_STOP=1 \
  --file "$ROOT_DIR/supabase/migrations/20260705023833_enforce_rls_on_exposed_tables.sql"

psql "$DATABASE_URL" --set ON_ERROR_STOP=1 --command \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('compliance_exceptions','compliance_presets','compliance_rules','export_jobs','jurisdictions','project_compliance_records','workspace_invites','workspace_members','workspaces') ORDER BY tablename;"

echo "Week 2 migrations completed."
