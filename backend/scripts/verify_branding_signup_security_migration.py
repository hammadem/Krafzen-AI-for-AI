"""Rehearse the branding RLS and paid-only signup migration on disposable CI PG.

This intentionally refuses all nonlocal connections. It never connects to Supabase.
"""
import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/20261121000000_branding_rls_and_signup_hardening.sql"
NEW_USER = "00000000-0000-0000-0000-000000000222"
OLD_USER = "00000000-0000-0000-0000-000000000223"
BRANDING = (
    "branding_audit_events", "branding_drafts",
    "branding_versions", "report_branding_snapshots",
)


def run():
    # Never allow libpq hostaddr/service query overrides or cloud credentials.
    raw = os.getenv("DATABASE_URL", "")
    try:
        url = urlsplit(raw)
        safe = (
            url.scheme == "postgresql"
            and url.hostname in {"localhost", "127.0.0.1"}
            and url.username == "krafzen_ci"
            and url.path == "/krafzen_ci"
            and url.port == 5432
            and not url.query and not url.fragment
        )
    except ValueError:
        safe = False
    if not safe:
        raise RuntimeError("Only disposable local krafzen_ci PostgreSQL is permitted")
    with psycopg2.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS auth")
            for role in ("anon", "authenticated", "service_role"):
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,))
                if cur.fetchone() is None:
                    cur.execute(f"CREATE ROLE {role} NOLOGIN")
            # The payment CI step may already have created user_subscriptions.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.user_subscriptions(
                    user_id UUID PRIMARY KEY, plan_name TEXT,
                    plan_tier TEXT, subscription_status TEXT,
                    remaining_minutes NUMERIC,
                    trial_requests_total INTEGER,
                    trial_requests_remaining INTEGER,
                    plan_requests_total INTEGER,
                    plan_requests_remaining INTEGER,
                    updated_at TIMESTAMPTZ)
            """)
            cur.execute("ALTER TABLE public.user_subscriptions ADD COLUMN IF NOT EXISTS remaining_minutes NUMERIC")
            cur.execute("CREATE TABLE IF NOT EXISTS auth.users(id UUID PRIMARY KEY)")
            for table in BRANDING:
                cur.execute("CREATE TABLE IF NOT EXISTS public." + table + " (id INTEGER PRIMARY KEY)")
                cur.execute("GRANT SELECT, INSERT ON public." + table +
                            " TO PUBLIC, anon, authenticated")
                cur.execute("INSERT INTO public." + table + " (id) VALUES (1) ON CONFLICT DO NOTHING")
            cur.execute(
                """INSERT INTO public.user_subscriptions
                (user_id, plan_name, plan_tier, subscription_status,
                 remaining_minutes, trial_requests_total, trial_requests_remaining,
                 plan_requests_total, plan_requests_remaining)
                VALUES (%s, 'starter', 'starter', 'active',
                0, 15, 15, 50, 37) ON CONFLICT DO NOTHING""",
                (OLD_USER,),
            )
            script = MIGRATION.read_text(encoding="utf-8")
            cur.execute(script)
            cur.execute(script)  # Repeat-safe migration.
            for table in BRANDING:
                cur.execute(
                    "SELECT relrowsecurity FROM pg_class WHERE oid = %s::regclass",
                    ("public." + table,),
                )
                assert cur.fetchone() == (True,), table
                # A table-level GRANT is not enough to bypass RLS. No explicit
                # policy on these sensitive tables means no row visibility.
                cur.execute(
                    "SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename=%s",
                    (table,),
                )
                assert cur.fetchone() == (0,), table

                # Verify zero effective browser privileges, rather than
                # relying only on row-level security policy filtering.
                for role in ("anon", "authenticated"):
                    cur.execute(
                        "SELECT has_table_privilege(%s,%s,'SELECT'),"
                        "has_table_privilege(%s,%s,'INSERT')",
                        (role, "public." + table, role, "public." + table),
                    )
                    assert cur.fetchone() == (False, False), (table, role)
                cur.execute(
                    "SELECT has_table_privilege('service_role',%s,'SELECT')",
                    ("public." + table,),
                )
                assert cur.fetchone() == (True,), table

            cur.execute(
                "SELECT trial_requests_total,trial_requests_remaining,plan_requests_remaining "
                "FROM public.user_subscriptions WHERE user_id=%s", (OLD_USER,),
            )
            assert cur.fetchone() == (0, 0, 37), "Existing paid balance changed"
            for role in ("anon", "authenticated"):
                cur.execute(
                    "SELECT has_function_privilege(%s,'public.handle_new_user()','EXECUTE')",
                    (role,),
                )
                assert cur.fetchone() == (False,), role
            cur.execute("""
                SELECT p.prosecdef, p.proconfig FROM pg_proc p
                WHERE p.oid = 'public.handle_new_user()'::regprocedure
            """)
            secdef, settings = cur.fetchone()
            assert secdef and settings and any(value in ("search_path=", 'search_path=""') for value in settings)

            cur.execute("""CREATE TRIGGER test_new_user_signup
                AFTER INSERT ON auth.users FOR EACH ROW
                EXECUTE FUNCTION public.handle_new_user()""")
            cur.execute("INSERT INTO auth.users(id) VALUES (%s)", (NEW_USER,))
            cur.execute(
                "SELECT trial_requests_total,trial_requests_remaining,plan_requests_remaining "
                "FROM public.user_subscriptions WHERE user_id=%s", (NEW_USER,),
            )
            assert cur.fetchone() == (0, 0, 0), "New signup still has free credits"
    print("PASS: four branding tables: RLS on, zero anon/auth privileges, service role retained, secure signup and paid credits intact.")


if __name__ == "__main__":
    run()
