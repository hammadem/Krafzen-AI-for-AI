"""Verify the proposed ACL in a disposable loopback Supabase stack only."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import secrets
import psycopg2
import requests
from verify_customer_acceptance import configure

TABLES = ["projects","jobs","chat_sessions","chat_messages","message_feedback","notifications","export_jobs","workspaces","workspace_members","workspace_invites","organization_residency","residency_audit_events","payment_history"]
def main():
    api, dsn, role, anon = configure()
    migration = Path(__file__).resolve().parents[1] / "app/db/migrations/024_paid_workspace_browser_acl.sql"
    with psycopg2.connect(dsn) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(migration.read_text())
            cur.execute(migration.with_name("025_project_metadata.sql").read_text())
            cur.execute(migration.with_name("026_field_observation_notes.sql").read_text())
            for table in TABLES:
                for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"):
                    for browser_role in ("anon", "authenticated"):
                        cur.execute("SELECT has_table_privilege(%s, %s, %s)", (browser_role, "public."+table, privilege))
                        assert not cur.fetchone()[0], (table, browser_role, privilege)
                for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                    cur.execute("SELECT has_table_privilege('service_role', %s, %s)", ("public."+table, privilege))
                    assert cur.fetchone()[0], (table, "service_role", privilege)

    email = "acl-qa-" + secrets.token_hex(8) + "@example.com"
    password = secrets.token_urlsafe(32)
    r = requests.post(api+"/auth/v1/admin/users", headers={"apikey":role, "Authorization":"Bearer "+role},
                      json={"email":email,"password":password,"email_confirm":True}, timeout=20)
    assert r.status_code in (200,201), r.status_code
    uid = r.json()["id"]
    r = requests.post(api+"/auth/v1/token?grant_type=password",headers={"apikey":anon},
                      json={"email":email,"password":password},timeout=20)
    assert r.status_code == 200, r.status_code
    auth = {"Authorization":"Bearer "+r.json()["access_token"]}
    browser = {"apikey":anon, **auth, "Prefer":"return=representation"}

    def denied(method, path, payload):
        r = requests.request(method, api+"/rest/v1/"+path, headers=browser, json=payload, timeout=20)
        assert r.status_code in (401,403), (method,path,r.status_code)

    denied("POST","projects",{"user_id":uid,"input_text":"Unpaid direct REST creation"})
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""UPDATE public.user_subscriptions SET plan_name='starter',
            plan_tier='starter', billing_cycle='monthly', subscription_status='active',
            stripe_subscription_id=%s, plan_requests_total=50, plan_requests_remaining=50,
            plan_requests_reset_date=%s WHERE user_id=%s""",
            ("qa-acl-"+uid,datetime.now(timezone.utc)+timedelta(days=30),uid))
        assert cur.rowcount == 1

    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        r = client.post("/api/v1/projects/", headers=auth, json={"input_text":"ACL QA project"})
        assert r.status_code == 201, r.status_code
        pid = r.json()["id"]
        r = client.post("/api/v1/jobs/", headers=auth, json={"project_id":pid})
        assert r.status_code == 201, r.status_code
        jid = r.json()["id"]
        denied("PATCH","jobs?id=eq."+jid,{"status":"completed"})
        denied("DELETE","projects?id=eq."+pid,{})
        assert client.get("/api/v1/projects/"+pid,headers=auth).status_code == 200
    print("PASS: browser mutation grants removed; unpaid direct REST write and paid job forgery denied; entitled backend project/job operations work.")

if __name__ == "__main__":
    main()
