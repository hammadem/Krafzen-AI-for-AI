"""Verify the project archive migration on isolated local CI PostgreSQL."""

import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2

SQL = Path(__file__).resolve().parents[2] / "supabase/migrations/20261118020000_project_archive_lifecycle.sql"


def main() -> None:
    u = urlsplit(os.getenv("DATABASE_URL", ""))
    if u.hostname not in {"127.0.0.1", "localhost"} or u.username != "krafzen_ci":
        raise RuntimeError("Only disposable local CI PostgreSQL is allowed")
    with psycopg2.connect(os.environ["DATABASE_URL"]) as db:
        with db.cursor() as cur:
            cur.execute(
                """CREATE TABLE public.projects (
                    id uuid PRIMARY KEY, user_id uuid NOT NULL,
                    created_at timestamptz NOT NULL DEFAULT NOW()
                )"""
            )
            migration = SQL.read_text(encoding="utf-8")
            cur.execute(migration)
            cur.execute(migration)
            cur.execute(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_schema='public' AND table_name='projects'
                     AND column_name IN ('archived_at','archived_by','restored_at','restored_by')
                """
            )
            assert {r[0] for r in cur.fetchall()} == {
                "archived_at", "archived_by", "restored_at", "restored_by"
            }
            cur.execute(
                """INSERT INTO public.projects (id,user_id) VALUES (
                   '00000000-0000-0000-0000-000000000011',
                   '00000000-0000-0000-0000-000000000001')"""
            )
            cur.execute(
                """UPDATE public.projects SET archived_at=NOW(),
                   archived_by='00000000-0000-0000-0000-000000000001'
                   WHERE id='00000000-0000-0000-0000-000000000011'"""
            )
            cur.execute("SELECT COUNT(*) FROM public.projects WHERE archived_at IS NOT NULL")
            assert cur.fetchone() == (1,)
            cur.execute(
                """UPDATE public.projects SET archived_at=NULL, archived_by=NULL,
                   restored_at=NOW(), restored_by='00000000-0000-0000-0000-000000000001'
                   WHERE id='00000000-0000-0000-0000-000000000011'"""
            )
            cur.execute("SELECT COUNT(*) FROM public.projects WHERE archived_at IS NULL AND restored_by IS NOT NULL")
            assert cur.fetchone() == (1,)
    print("Project archive migration: repeated apply, archive, and restore verified")


if __name__ == "__main__":
    main()
