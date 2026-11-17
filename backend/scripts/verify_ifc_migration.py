"""Validate the IFC column migration against throwaway PostgreSQL only.

The script refuses remote databases even if DATABASE_URL is misconfigured.
It intentionally does NOT claim to test the entire legacy schema or auth/RLS.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import psycopg2


def main():
    url = os.environ.get("DATABASE_URL", "")
    parsed = urlparse(url)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.username != "krafzen_ci":
        raise RuntimeError("Migration test must target only isolated local CI PostgreSQL")

    migration = (
        Path(__file__).resolve().parents[2]
        / "supabase" / "migrations" / "20261118000000_file_import_metadata.sql"
    )
    content = migration.read_text(encoding="utf-8")
    with psycopg2.connect(url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE public.files (id uuid PRIMARY KEY)")
            for _ in range(2):
                cursor.execute(content)

            cursor.execute(
                """
                SELECT data_type FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='files'
                  AND column_name='import_metadata'
                """
            )
            row = cursor.fetchone()
            if row != ("jsonb",):
                raise AssertionError(f"IFC import column missing/wrong type: {row}")

            cursor.execute(
                "INSERT INTO public.files (id, import_metadata) VALUES (%s, %s::jsonb)",
                ("00000000-0000-0000-0000-000000000111", '{"type":"ifc","schema":"IFC4"}'),
            )
            cursor.execute(
                "SELECT import_metadata->>'schema' FROM public.files LIMIT 1"
            )
            assert cursor.fetchone() == ("IFC4",)

    print("IFC metadata migration applied twice; JSONB insert/read verified.")


if __name__ == "__main__":
    main()
