"""Real browser-to-API-to-Supabase acceptance on disposable infrastructure.

No cloud credentials, browser request mocks or live subscriptions. The sole
paid entitlement fixture is inserted into the checked loopback QA database.
"""
import io
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import ezdxf
import psycopg2
import requests
from playwright.sync_api import sync_playwright, expect

from verify_customer_acceptance import configure

ROOT = Path(__file__).resolve().parents[2]
API = "http://127.0.0.1:8000"
WEB = "http://127.0.0.1:3000"


def wait_http(url, process, seconds=150):
    for _ in range(seconds):
        if process.poll() is not None:
            raise RuntimeError("Local application process exited")
        try:
            if requests.get(url, timeout=2).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("Local application unavailable")


def main():
    supabase, dsn, role, anon = configure()
    env = {**os.environ, "NEXT_PUBLIC_SUPABASE_URL": supabase,
           "NEXT_PUBLIC_SUPABASE_ANON_KEY": anon, "NEXT_PUBLIC_API_URL": API,
           "NEXT_TELEMETRY_DISABLED": "1", "ALLOWED_ORIGINS": WEB}
    # Public browser build/runtime only receives publishable values.
    frontend_env = {k: v for k,v in env.items() if k not in {
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY", "SUPABASE_JWT_SECRET",
        "GEMINI_API_KEY", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"}}
    output = Path(os.environ["BROWSER_ACCEPTANCE_RESULT"])
    evidence = []
    def note(step):
        evidence.append({"step": step, "status": "PASS"})
        output.write_text(json.dumps({"scope": "isolated real Chromium frontend acceptance; local QA entitlement", "checks": evidence}, indent=2))
        print("BROWSER PASS: " + step, flush=True)
    def account(paid=False):
        email = "browser-qa-" + secrets.token_hex(8) + "@example.com"
        password = "Qa!" + secrets.token_urlsafe(25) + "9a"
        r = requests.post(supabase+"/auth/v1/admin/users",
          headers={"apikey":role,"Authorization":"Bearer "+role},
          json={"email":email,"password":password,"email_confirm":True},timeout=20)
        assert r.status_code in (200,201)
        uid = r.json()["id"]
        if paid:
            with psycopg2.connect(dsn) as con, con.cursor() as cur:
                cur.execute("""UPDATE public.user_subscriptions SET plan_name='starter',
                    plan_tier='starter', billing_cycle='monthly', subscription_status='active',
                    stripe_subscription_id=%s, plan_requests_total=50, plan_requests_remaining=50,
                    plan_requests_reset_date=%s WHERE user_id=%s""",
                    ("browser-fixture-"+uid,datetime.now(timezone.utc)+timedelta(days=30),uid))
                assert cur.rowcount == 1
        session=requests.post(supabase+"/auth/v1/token?grant_type=password",headers={"apikey":anon},
            json={"email":email,"password":password},timeout=20)
        assert session.status_code==200
        return email,password,{"Authorization":"Bearer "+session.json()["access_token"]}

    backend_log = output.with_suffix(".backend.log")
    frontend_log = output.with_suffix(".frontend.log")
    processes=[]
    try:
        with backend_log.open("w") as backlog, frontend_log.open("w") as weblog:
            backend=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app",
                "--host","127.0.0.1","--port","8000"],cwd=ROOT/"backend",env=env,
                stdout=backlog,stderr=subprocess.STDOUT)
            processes.append(backend)
            wait_http(API+"/health",backend)
            frontend=subprocess.Popen(["npm","run","dev","--","--hostname","127.0.0.1"],
                cwd=ROOT/"frontend",env=frontend_env,stdout=weblog,stderr=subprocess.STDOUT)
            processes.append(frontend)
            wait_http(WEB+"/logincred",frontend)
            email,password,headers=account(True)
            unpaid_email,unpaid_password,_=account(False)
            names=["Browser residential QA","Browser commercial QA","Browser BIM QA"]
            projects=[]
            for name in names:
                r=requests.post(API+"/api/v1/projects/",headers=headers,json={"input_text":name},timeout=20)
                assert r.status_code==201
                pid=r.json()["id"]
                r=requests.post(API+"/api/v1/jobs/",headers=headers,json={"project_id":pid},timeout=20)
                assert r.status_code==201
                projects.append((pid,r.json()["id"]))
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                def login(context,email,password):
                    page=context.new_page()
                    page.set_default_timeout(60000)
                    page.goto(WEB+"/logincred",wait_until="domcontentloaded")
                    page.get_by_placeholder("Email",exact=True).fill(email)
                    page.get_by_placeholder("Password",exact=True).fill(password)
                    page.get_by_role("button",name="Submit",exact=True).click()
                    page.wait_for_url("**/workspace",timeout=60000) if email != unpaid_email else page.wait_for_url("**/pricing",timeout=60000)
                    return page
                with browser.new_context() as context:
                    page=login(context,unpaid_email,unpaid_password)
                    page.goto(WEB+"/workspace/projects")
                    expect(page.get_by_role("heading",name="An active paid subscription is required")).to_be_visible(timeout=60000)
                    note("Real browser login: unpaid customer cannot enter workspace")
                with browser.new_context() as context:
                    page=login(context,email,password)
                    page.goto(WEB+"/workspace/projects")
                    expect(page.get_by_role("heading",name="Your Projects")).to_be_visible(timeout=60000)
                    for name in names:
                        expect(page.get_by_text(name,exact=True)).to_be_visible()
                    note("Actual authenticated frontend displays three persisted projects")
                    page.goto(WEB+"/workspace/cad")
                    expect(page.get_by_role("heading",name="Parametric CAD Room")).to_be_visible(timeout=60000)
                    pid,jid=projects[0]
                    page.get_by_label("CAD project",exact=True).select_option(pid)
                    page.get_by_label("CAD job",exact=True).select_option(jid)
                    for label,value in [("Room name","Browser measured room"),("Exterior width (m)","5"),("Exterior length (m)","4"),("Wall thickness (m)","0.2")]:
                        page.get_by_label(label,exact=True).fill(value)
                    page.get_by_role("button",name="Generate and save DXF").click()
                    expect(page.get_by_role("heading",name="Saved drawing")).to_be_visible(timeout=60000)
                    page.get_by_role("button",name="Get authenticated DXF download").click()
                    link=page.get_by_role("link",name="Download saved DXF")
                    expect(link).to_be_visible()
                    signed=link.get_attribute("href")
                    assert urlsplit(signed).hostname in {"127.0.0.1","localhost"}
                    raw=requests.get(signed,timeout=20)
                    assert raw.status_code==200
                    doc=ezdxf.read(io.StringIO(raw.content.decode("utf-8")))
                    assert doc.header["$INSUNITS"]==6 and len(doc.modelspace().query("DIMENSION"))>=2
                    note("Browser creates real dimensioned DXF and downloads verified private bytes")
                    page.goto(WEB+"/workspace/projects")
                    page.get_by_role("button",name="Archive "+names[0],exact=True).click()
                    page.get_by_role("button",name="Confirm archive",exact=True).click()
                    expect(page.get_by_text(names[0],exact=True)).to_have_count(0)
                    page.goto(WEB+"/workspace/archive")
                    page.get_by_role("button",name="Restore "+names[0],exact=True).click()
                    expect(page.get_by_role("button",name="Restore "+names[0],exact=True)).to_have_count(0)
                    note("Browser archive and restore workflow")
                # New context has no previous browser storage or cookies.
                with browser.new_context() as context:
                    page=login(context,email,password)
                    page.goto(WEB+"/workspace/projects")
                    for name in names:
                        expect(page.get_by_text(name,exact=True)).to_be_visible(timeout=60000)
                    response=requests.get(API+"/api/v1/files/",headers=headers,params={"job_id":projects[0][1]},timeout=20)
                    assert response.status_code==200 and any(x.get("name")=="Browser measured room.dxf" for x in response.json())
                    note("Close browser, new login, all three projects and generated file persist")
                browser.close()
    finally:
        for proc in reversed(processes):
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill()


if __name__=="__main__":
    main()
