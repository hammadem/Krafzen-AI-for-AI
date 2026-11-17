"""Exercise the payment ledger on disposable local PostgreSQL only."""

import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "supabase/migrations/20261118010000_paid_webhook_atomic_ledger.sql"
USER = "00000000-0000-0000-0000-000000000111"


def apply(cursor, event_id, resource_id, kind="paid", sub="sub_001", occurred="2026-01-18 12:00:00+00", user=USER):
    cursor.execute(
        """SELECT public.apply_paid_webhook_event(
          %s,%s,%s,%s,%s::uuid,%s,%s,%s,%s,%s::timestamptz)""",
        ("stripe", event_id, kind, resource_id, user, sub, "cus_001", "starter", "monthly", occurred),
    )
    return cursor.fetchone()[0]


def main():
    parsed = urlsplit(os.getenv("DATABASE_URL", ""))
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.username != "krafzen_ci":
        raise RuntimeError("Only disposable local CI databases are permitted")
    with psycopg2.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE ROLE anon NOLOGIN")
            cur.execute("CREATE ROLE authenticated NOLOGIN")
            cur.execute("CREATE ROLE service_role NOLOGIN")
            cur.execute(
                """CREATE TABLE public.user_subscriptions(
                    user_id uuid PRIMARY KEY, stripe_subscription_id text,
                    stripe_customer_id text, plan_name text, plan_tier text,
                    billing_cycle text, subscription_status text,
                    trial_requests_total int, trial_requests_remaining int,
                    plan_requests_total int, plan_requests_remaining int,
                    plan_requests_reset_date timestamptz,
                    updated_at timestamptz
                )"""
            )
            cur.execute("INSERT INTO public.user_subscriptions(user_id) VALUES (%s)", (USER,))
            sql = SQL.read_text(encoding="utf-8")
            cur.execute(sql)
            cur.execute(sql)  # migration is repeatable
            signature = "public.apply_paid_webhook_event(text,text,text,text,uuid,text,text,text,text,timestamp with time zone)"
            for role in ("anon", "authenticated"):
                cur.execute("SELECT has_function_privilege(%s,%s,'EXECUTE')", (role, signature))
                assert cur.fetchone() == (False,), role
                cur.execute("SELECT has_table_privilege(%s,'public.payment_webhook_events','SELECT')", (role,))
                assert cur.fetchone() == (False,), role
            cur.execute("SELECT has_function_privilege('service_role',%s,'EXECUTE')", (signature,))
            assert cur.fetchone() == (True,)

            assert apply(cur, "evt_001", "checkout_001") == "applied"
            assert apply(cur, "evt_001", "checkout_001") == "duplicate"
            assert apply(cur, "evt_002", "checkout_001") == "duplicate"
            cur.execute("SELECT plan_requests_remaining,subscription_status FROM public.user_subscriptions WHERE user_id=%s", (USER,))
            assert cur.fetchone() == (50, "active")

            # Spending 1 request must not be refunded by a duplicated checkout.
            cur.execute("UPDATE public.user_subscriptions SET plan_requests_remaining=49 WHERE user_id=%s", (USER,))
            assert apply(cur, "evt_003", "checkout_001") == "duplicate"
            cur.execute("SELECT plan_requests_remaining FROM public.user_subscriptions WHERE user_id=%s", (USER,))
            assert cur.fetchone() == (49,)

            assert apply(cur, "evt_004", "invoice_renewal", occurred="2026-01-18 13:00:00+00") == "applied"
            cur.execute("SELECT plan_requests_remaining FROM public.user_subscriptions WHERE user_id=%s", (USER,))
            assert cur.fetchone() == (50,)

            # Out-of-order older paid event cannot reset a newer balance.
            cur.execute("UPDATE public.user_subscriptions SET plan_requests_remaining=48 WHERE user_id=%s", (USER,))
            assert apply(cur, "evt_005", "checkout_old", occurred="2026-01-18 12:30:00+00") == "ignored"
            cur.execute("SELECT plan_requests_remaining FROM public.user_subscriptions WHERE user_id=%s", (USER,))
            assert cur.fetchone() == (48,)

            # Old-subscription cancellation cannot revoke a different subscription.
            assert apply(cur, "evt_006", "sub_old", kind="canceled", sub="sub_other", occurred="2026-01-18 13:30:00+00") == "ignored"
            cur.execute("SELECT subscription_status FROM public.user_subscriptions WHERE user_id=%s", (USER,))
            assert cur.fetchone() == ("active",)

            assert apply(cur, "evt_007", "invoice_failed", kind="past_due", occurred="2026-01-18 14:00:00+00") == "applied"
            cur.execute("SELECT subscription_status FROM public.user_subscriptions WHERE user_id=%s", (USER,))
            assert cur.fetchone() == ("past_due",)

            # Transactional rollback on missing signup row means a later retry
            # can succeed after the account exists.
            try:
                cur.execute("SAVEPOINT missing_account")
                apply(cur, "evt_missing", "checkout_missing", user="00000000-0000-0000-0000-000000000999")
                raise AssertionError("Missing account did not fail")
            except psycopg2.Error:
                cur.execute("ROLLBACK TO SAVEPOINT missing_account")
            cur.execute("SELECT count(*) FROM public.payment_webhook_events WHERE event_id='evt_missing'")
            assert cur.fetchone() == (0,)

            cur.execute("SELECT COUNT(*) FROM public.payment_webhook_events WHERE outcome='applied'")
            assert cur.fetchone()[0] >= 3
    print("Paid webhook ledger verified: repeat migration, RPC ACLs, idempotency, retries, stale ordering, cancellation.")


if __name__ == "__main__":
    main()
