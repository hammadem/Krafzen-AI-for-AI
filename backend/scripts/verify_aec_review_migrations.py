"""Exercise new AEC review/as-built schema on isolated PostgreSQL, never live DB."""
import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = [
    ROOT / "supabase/migrations/20261123000000_asbuilt_comparisons.sql",
    ROOT / "supabase/migrations/20261123010000_drawing_redlines.sql",
    ROOT / "supabase/migrations/20261123020000_field_inspections.sql",
    ROOT / "supabase/migrations/20261124000000_compliance_assessments.sql",
    ROOT / "supabase/migrations/20261124010000_field_photo_evidence.sql",
    ROOT / "supabase/migrations/20261124020000_bim_spatial_screenings.sql",
]


def require_disposable_database_url(raw: str) -> str:
    """Refuse cloud hosts and libpq URI overrides before any SQL executes.

    Local CI is intentionally pinned to the PostgreSQL service user, database,
    loopback hostname and port. The caller cannot pass query parameters such
    as hostaddr to redirect a seemingly local database URL.
    """
    try:
        parsed = urlsplit(raw)
        allowed = (
            parsed.scheme == "postgresql"
            and parsed.hostname in {"localhost", "127.0.0.1"}
            and parsed.port == 5432
            and parsed.username == "krafzen_ci"
            and parsed.path == "/krafzen_ci"
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        allowed = False
    if not allowed:
        raise RuntimeError(
            "AEC schema migration verification is restricted to disposable "
            "local CI PostgreSQL (krafzen_ci@127.0.0.1:5432/krafzen_ci)"
        )
    return raw


def main():
    url = require_disposable_database_url(os.environ.get("DATABASE_URL", ""))
    with psycopg2.connect(url) as db:
        db.autocommit = True
        with db.cursor() as cursor:
            cursor.execute("create schema if not exists auth")
            for role in ("anon", "authenticated", "service_role"):
                cursor.execute(
                    "select 1 from pg_roles where rolname = %s", (role,)
                )
                if not cursor.fetchone():
                    cursor.execute(f"create role {role} nologin")
            cursor.execute("create table if not exists auth.users (id uuid primary key)")
            cursor.execute("create table if not exists public.projects (id uuid primary key)")
            cursor.execute("create table if not exists public.files (id uuid primary key)")

            # Both migrations must be safe to re-run after partial deployment.
            for migration in MIGRATIONS:
                query = migration.read_text(encoding="utf-8")
                for _ in range(2):
                    cursor.execute(query)

            for table in ("asbuilt_comparisons", "drawing_redlines", "field_inspections", "compliance_assessments", "field_photos", "bim_spatial_screenings"):
                cursor.execute(
                    "select relrowsecurity from pg_class "
                    "where oid = %s::regclass",
                    (f"public.{table}",),
                )
                record = cursor.fetchone()
                assert record and record[0], f"RLS not active for {table}"
                cursor.execute(
                    "select has_table_privilege('anon', %s, 'SELECT'),"
                    "has_table_privilege('authenticated', %s, 'INSERT'),"
                    "has_table_privilege('service_role', %s, 'INSERT')",
                    (f"public.{table}", f"public.{table}", f"public.{table}"),
                )
                grants = cursor.fetchone()
                assert grants == (False, False, True), (table, grants)

            cursor.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'public' and table_name = 'drawing_redlines'"
            )
            columns = {name for (name,) in cursor.fetchall()}
            for col in ("project_id", "file_id", "file_version", "created_by",
                        "kind", "x", "y", "x2", "y2", "comment", "severity", "status"):
                assert col in columns, f"Redlines missing {col}"

            # Earlier isolated migration smoke tests may have created a
            # richer projects/files schema with additional NOT NULL columns.
            # Verify table constraints from the database catalog instead of
            # writing incompatible fixture rows into those independent stubs.
            cursor.execute(
                "select conname from pg_constraint "
                "where conrelid = 'public.drawing_redlines'::regclass "
                "and contype = 'c'"
            )
            checks = {name for (name,) in cursor.fetchall()}
            for required in (
                "drawing_redlines_x_check", "drawing_redlines_y_check",
                "drawing_redlines_severity_check", "drawing_redlines_status_check",
            ):
                assert required in checks, f"Missing review constraint {required}"

            cursor.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'public' and table_name = 'field_inspections'"
            )
            field_columns = {name for (name,) in cursor.fetchall()}
            for field in ("id","project_id","title","description","created_by",
                          "location_label","discipline","severity","status",
                          "observed_at","created_at","resolved_at"):
                assert field in field_columns, f"Missing field observation {field}"
            cursor.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'public' and table_name = 'compliance_assessments'"
            )
            compliance_columns = {name for (name,) in cursor.fetchall()}
            for col in ("id", "project_id", "source_file_id", "created_by",
                        "jurisdiction", "measurements", "result", "review_status", "created_at"):
                assert col in compliance_columns, f"Missing compliance assessment {col}"
            cursor.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'public' and table_name = 'field_photos'"
            )
            photo_columns = {name for (name,) in cursor.fetchall()}
            for col in ("id", "project_id", "inspection_id", "created_by",
                        "bucket", "path", "mime_type", "size_bytes", "source_metadata"):
                assert col in photo_columns, f"Missing field photo evidence column {col}"
            cursor.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'public' and table_name = 'bim_spatial_screenings'"
            )
            spatial_columns = {name for (name,) in cursor.fetchall()}
            for col in ("id", "project_id", "primary_file_id", "secondary_file_id",
                        "created_by", "alignment_user_asserted", "result", "created_at"):
                assert col in spatial_columns, f"Missing BIM screen evidence column {col}"
            cursor.execute(
                "select conname from pg_constraint "
                "where conrelid = 'public.bim_spatial_screenings'::regclass "
                "and contype = 'c'"
            )
            spatial_checks = {name for (name,) in cursor.fetchall()}
            assert "bim_spatial_screenings_distinct_files" in spatial_checks
            print("PASS: six AEC migrations applied twice; RLS/grants/constraints verified")


if __name__ == "__main__":
    main()
