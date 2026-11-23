"""Exercise new AEC review/as-built schema on isolated PostgreSQL, never live DB."""
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = [
    ROOT / "supabase/migrations/20261123000000_asbuilt_comparisons.sql",
    ROOT / "supabase/migrations/20261123010000_drawing_redlines.sql",
]


def main():
    url = os.environ["DATABASE_URL"]
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

            for table in ("asbuilt_comparisons", "drawing_redlines"):
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

            # Real constraint test: malformed normalized coordinates must fail.
            cursor.execute(
                "insert into auth.users (id) values "
                "('00000000-0000-0000-0000-000000000001')"
            )
            cursor.execute(
                "insert into public.projects (id) values "
                "('00000000-0000-0000-0000-000000000002')"
            )
            cursor.execute(
                "insert into public.files (id) values "
                "('00000000-0000-0000-0000-000000000003')"
            )
            try:
                cursor.execute(
                    "insert into public.drawing_redlines "
                    "(project_id,file_id,created_by,kind,x,y,comment,severity) "
                    "values (%s,%s,%s,'comment',1.5,0.5,'invalid','info')",
                    (
                        "00000000-0000-0000-0000-000000000002",
                        "00000000-0000-0000-0000-000000000003",
                        "00000000-0000-0000-0000-000000000001",
                    ),
                )
            except psycopg2.errors.CheckViolation:
                pass
            else:
                raise AssertionError("Out-of-bounds review markup was inserted")

            print("PASS: two AEC migrations applied twice; RLS/grants/constraints verified")


if __name__ == "__main__":
    main()
