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
    def note(step,status="PASS"):
        evidence.append({"step": step, "status": status})
        output.write_text(json.dumps({"scope": "isolated real Chromium frontend acceptance; local QA entitlement", "checks": evidence}, indent=2))
        print("BROWSER "+status+": " + step, flush=True)
    def account(paid=False):
        email = "browser-acceptance-" + secrets.token_hex(12) + "@example.com"
        password = "Qa!" + secrets.token_urlsafe(32) + "9a"
        assert 32 < len(email) <= 254 and 32 < len(password) <= 72, "Exercise the corrected login validation limits"
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
            preflight=requests.options(API+"/api/v1/projects/",headers={"Origin":WEB,"Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"authorization,content-type,apikey"},timeout=20)
            assert preflight.headers.get("Access-Control-Allow-Origin")==WEB
            assert {"authorization","content-type","apikey"} <= {h.strip().lower() for h in preflight.headers.get("Access-Control-Allow-Headers","").split(",")}
            note("Actual backend CORS preflight permits authenticated frontend API headers")
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
                    page.goto(WEB+"/logincred",wait_until="load")
                    expect(page.get_by_role("button",name="Submit",exact=True)).to_be_enabled()
                    observations=[]
                    page.on("response", lambda r: observations.append((urlsplit(r.url).path,r.status)) if "/auth/v1/token" in r.url or "/api/v1/payments/subscription-status" in r.url else None)
                    page.get_by_placeholder("Email",exact=True).fill(email)
                    page.get_by_placeholder("Password",exact=True).fill(password)
                    page.get_by_role("button",name="Submit",exact=True).click()
                    try:
                        page.wait_for_url("**/workspace" if email != unpaid_email else "**/pricing",timeout=60000,wait_until="domcontentloaded")
                    except Exception:
                        print("Login diagnostics: current path", urlsplit(page.url).path, "auth/subscription HTTP observations", observations, flush=True)
                        print("Invalid form inputs:",page.locator("input[aria-invalid=true]").count(),flush=True)
                        raise
                    return page
                with browser.new_context() as context:
                    expired=context.new_page()
                    expired.goto(WEB+"/?error=access_denied&error_code=otp_expired",wait_until="domcontentloaded")
                    expect(expired.locator("p[role=alert]")).to_contain_text("invalid or has expired",timeout=60000)
                    expired.get_by_role("link",name="Request a new verification email").click()
                    expect(expired.get_by_role("heading",name="Resend verification email")).to_be_visible(timeout=60000)
                    expired.close()
                    note("Expired verification fallback stays on hosted origin and offers resend")
                    provider_page=context.new_page()
                    provider_page.goto(WEB+"/login",wait_until="load")
                    provider_page.get_by_role("button",name="Google").click()
                    expect(provider_page.locator("p[role=alert]")).to_contain_text("not enabled",timeout=30000)
                    assert urlsplit(provider_page.url).netloc==urlsplit(WEB).netloc
                    note("Disabled Google OAuth stays on application and offers email fallback")
                    provider_page.close()
                    validation_page=context.new_page()
                    validation_page.goto(WEB+"/logincred",wait_until="load")
                    expect(validation_page.get_by_role("button",name="Submit",exact=True)).to_be_enabled()
                    validation_page.get_by_placeholder("Email",exact=True).fill("not-an-email")
                    validation_page.get_by_role("button",name="Submit",exact=True).click()
                    expect(validation_page.get_by_text("Enter a valid email address.",exact=True)).to_be_visible()
                    expect(validation_page.get_by_text("Password is required.",exact=True)).to_be_visible()
                    validation_page.close()
                    note("Browser login validation gives correct email and password errors")
                    page=login(context,unpaid_email,unpaid_password)
                    page.goto(WEB+"/workspace/projects")
                    expect(page.get_by_role("heading",name="An active paid subscription is required")).to_be_visible(timeout=60000)
                    note("Real browser login with email and password longer than 32 characters: unpaid customer cannot enter workspace")
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
                    expect(link).to_be_visible(timeout=60000)
                    signed=link.get_attribute("href")
                    assert urlsplit(signed).hostname in {"127.0.0.1","localhost"}
                    raw=requests.get(signed,timeout=20)
                    assert raw.status_code==200
                    doc=ezdxf.read(io.StringIO(raw.content.decode("utf-8")))
                    assert doc.header["$INSUNITS"]==6 and len(doc.modelspace().query("DIMENSION"))>=2
                    note("Browser creates real dimensioned DXF and downloads verified private bytes")
                    saved_files=requests.get(API+"/api/v1/files/",headers=headers,params={"job_id":jid},timeout=20)
                    assert saved_files.status_code==200
                    fid=next(row["id"] for row in saved_files.json() if row["name"]=="Browser measured room.dxf")
                    # Main workspace, not the legacy ChatInterface.
                    page.goto(WEB+"/workspace",wait_until="domcontentloaded")
                    page.get_by_placeholder("Describe a design, or type /reference IFC walls to search references",exact=True).fill("count IFC model elements and IFC quantities")
                    page.get_by_role("button",name="Suggest AEC task",exact=True).click()
                    expect(page.get_by_text("Suggested task: bim · advisory only",exact=True)).to_be_visible()
                    assert page.get_by_text("ADA turning radius verified",exact=True).count()==0
                    note("Main workspace calls actual trained-model API; no hardcoded compliance pass")
                    page.goto(WEB+"/workspace/residency",wait_until="domcontentloaded")
                    expect(page.get_by_role("heading",name="USA Data Residency",exact=True)).to_be_visible()
                    expect(page.get_by_role("heading",name="Storage CDN and downloads",exact=True)).to_be_visible()
                    expect(page.get_by_text("End-to-end USA data residency is not certified.",exact=False)).to_be_visible()
                    note("Residency UI reads actual backend evidence and never certifies incomplete paths")
                    page.goto(WEB+"/workspace/compliance",wait_until="domcontentloaded")
                    page.get_by_label("Compliance project",exact=True).select_option(pid)
                    page.get_by_label("Compliance source file",exact=True).select_option(fid)
                    for label,value in [("State","QA State"),("Municipality","QA City"),("Project address","123 QA Road"),("Occupancy","B"),("Building type","Office")]:
                        page.get_by_label(label,exact=True).fill(value)
                    panel=page.locator("section").filter(has=page.get_by_role("heading",name="Multidiscipline code measurement catalog",exact=True))
                    expect(panel).to_be_visible()
                    panel.get_by_label("Adoption / ordinance reference",exact=True).fill("QA ordinance fixture")
                    panel.get_by_label("Reviewer name",exact=True).fill("Browser QA reviewer")
                    panel.get_by_label("Reviewer credential / jurisdiction (asserted)",exact=True).fill("Synthetic test only")
                    panel.get_by_label("Reviewer checked adoption and local amendments; no conflict with selected rules.",exact=True).check()
                    panel.get_by_label("Compliance catalog rule",exact=True).select_option("ADA-305.3-width")
                    panel.get_by_label("Adopted edition",exact=True).select_option("2010")
                    panel.get_by_label("Element / drawing reference",exact=True).fill("Browser A101")
                    panel.get_by_label("Measured value (in)",exact=True).fill("30")
                    panel.get_by_label("Qualified reviewer confirms the stated scope and exclusions.",exact=True).check()
                    panel.get_by_role("button",name="Add measurement to assessment",exact=True).click()
                    panel.get_by_role("button",name="Evaluate and save multidisciplinary evidence",exact=True).click()
                    expect(page.get_by_text("Element: Browser A101 · Source version: 1",exact=True)).to_be_visible()
                    expect(page.get_by_role("heading",name="Qualified reviewer declaration",exact=True)).to_be_visible()
                    for label,value in [("Declared reviewer name","Browser QA reviewer"),("Declared credential and jurisdiction","Synthetic QA fixture"),("Review reference (e.g. signed report ID)","BROWSER-REVIEW-001"),("Reviewer notes and unresolved provisions","Browser acceptance only, not a professional approval.")]:
                        page.get_by_label(label,exact=True).fill(value)
                    page.get_by_label("This is the reviewer's actual supplied declaration; credentials are not verified by KRAFZEN.",exact=True).check()
                    page.get_by_role("button",name="Record review declaration",exact=True).click()
                    expect(page.get_by_text("Recorded: reviewed · Browser QA reviewer",exact=True)).to_be_visible()
                    with page.expect_download() as download:
                        page.get_by_role("button",name="Download compliance PDF",exact=True).click()
                    from pypdf import PdfReader
                    text=" ".join(p.extract_text() or "" for p in PdfReader(str(download.value.path())).pages)
                    assert "BROWSER-REVIEW-001" in text
                    page.reload(wait_until="domcontentloaded")
                    page.get_by_label("Compliance project",exact=True).select_option(pid)
                    expect(page.get_by_text("Recorded: reviewed · Browser QA reviewer",exact=True)).to_be_visible()
                    note("Browser creates multidiscipline assessment, records review, downloads real PDF and reloads evidence")
                    page.goto(WEB+"/workspace/reviews",wait_until="domcontentloaded")
                    page.get_by_label("Review project",exact=True).select_option(pid)
                    page.get_by_label("Review drawing",exact=True).select_option(fid)
                    page.get_by_role("button",name="Inspect drawing geometry",exact=True).click()
                    expect(page.get_by_text("lines checked",exact=False)).to_be_visible()
                    # Actual browser-local inference, not a request mock.
                    from PIL import Image, ImageDraw, ImageFont
                    import math
                    symbol=Image.new("RGB",(24,24),"white")
                    for index in range(576):
                        if abs(math.hypot((index%24+.5)/12-1,(index//24+.5)/12-1)-.43)<.06:
                            symbol.putpixel((index%24,index//24),(0,0,0))
                    png=io.BytesIO();symbol.save(png,format="PNG")
                    page.get_by_label("Symbol crop",exact=True).set_input_files({"name":"circle.png","mimeType":"image/png","buffer":png.getvalue()})
                    expect(page.get_by_text("Experimental suggestion: pipe circle.",exact=False)).to_be_visible()
                    note("Reviews frontend calls real source diagnostic and executes local trained symbol inference")
                    page.goto(WEB+"/workspace/imports",wait_until="domcontentloaded")
                    page.get_by_label("Project for import",exact=True).select_option(pid)
                    page.get_by_label("Job for import",exact=True).select_option(jid)
                    expect(page.get_by_role("heading",name="Revit (RVT) desktop bridge",exact=True)).to_be_visible()
                    expect(page.get_by_role("button",name="Import Revit model through IFC",exact=True)).to_be_disabled()
                    page.get_by_label("Original RVT",exact=True).set_input_files({"name":"invalid.rvt","mimeType":"application/octet-stream","buffer":b"not a native Revit file"*40})
                    page.get_by_label("Revit-exported IFC",exact=True).set_input_files({"name":"invalid.ifc","mimeType":"application/octet-stream","buffer":b"invalid IFC"})
                    page.get_by_label("I confirm that the IFC was exported from this exact saved RVT revision.",exact=True).check()
                    page.get_by_role("button",name="Import Revit model through IFC",exact=True).click()
                    expect(page.get_by_text("Unsupported RVT container signature",exact=False)).to_be_visible()
                    note("Revit browser upload reaches backend, requires confirmation and rejects invalid native source; no Autodesk export claimed")
                    # Native scanner and OCR are prerequisites for genuine imports.
                    try:
                        scanner=subprocess.run(["clamscan","--version"],capture_output=True,timeout=10).returncode==0
                    except (OSError,subprocess.TimeoutExpired):
                        scanner=False
                    if scanner:
                        crop=Image.new("RGB",(1000,400),"white")
                        ImageDraw.Draw(crop).text((80,80),"ROOM 101 WIDTH 3200 MM",font=ImageFont.truetype("DejaVuSans.ttf",42),fill="black")
                        png=io.BytesIO();crop.save(png,format="PNG")
                        page.get_by_label("Choose a CAD, BIM or document file",exact=True).set_input_files({"name":"browser-ocr.png","mimeType":"image/png","buffer":png.getvalue()})
                        expect(page.get_by_text("Document scanned, parsed and saved to this project job.",exact=True)).to_be_visible(timeout=90000)
                        expect(page.get_by_text("OCR text (unverified)",exact=True)).to_be_visible()
                        page.get_by_text("OCR text (unverified)",exact=True).click()
                        expect(page.get_by_text("ROOM 101 WIDTH 3200 MM",exact=False)).to_be_visible()
                        note("Real browser image upload, native scanner, OCR persistence and visible recognized text")
                        from tests.unit.test_ifc_native_coordination import create_real_solid
                        import tempfile
                        with tempfile.TemporaryDirectory() as temp:
                            raw,_=create_real_solid(Path(temp)/"browser.ifc")
                        bp,bj=projects[2]
                        page.get_by_label("Project for import",exact=True).select_option(bp)
                        page.get_by_label("Job for import",exact=True).select_option(bj)
                        page.get_by_label("Choose a CAD, BIM or document file",exact=True).set_input_files({"name":"browser.ifc","mimeType":"application/octet-stream","buffer":raw})
                        expect(page.get_by_text("IFC model imported with parsed project and element metadata.",exact=True)).to_be_visible(timeout=90000)
                        response=requests.get(API+"/api/v1/files/",headers=headers,params={"job_id":bj},timeout=20)
                        model_id=next(row["id"] for row in response.json() if row["name"]=="browser.ifc")
                        page.goto(WEB+"/workspace/models",wait_until="domcontentloaded")
                        page.get_by_label("BIM project",exact=True).select_option(bp)
                        page.get_by_label("IFC model",exact=True).select_option(model_id)
                        page.get_by_role("button",name="Load actual 3D model",exact=True).click()
                        expect(page.get_by_role("img",name="Actual IFC 3D triangle geometry viewport",exact=True)).to_be_visible(timeout=90000)
                        page.get_by_label("IFC section axis",exact=True).select_option("z")
                        expect(page.get_by_label("IFC section position",exact=True)).to_be_visible()
                        slider=page.get_by_label("IFC section position",exact=True)
                        slider.focus()
                        slider.press("Home")
                        slider.press("ArrowRight")
                        expect(slider).to_have_value("1")
                        note("Browser imports real IFC, loads native triangle mesh and adjusts section cut")
                    else:
                        note("Browser OCR/IFC imports: scanner not available","BLOCKED")
                    registry=requests.get(API+"/api/v1/chat/model-registry",headers=headers,timeout=20)
                    assert registry.status_code==200,registry.status_code
                    assert registry.json()["reference_count"]==13
                    expect.set_options(timeout=60000)
                    page.goto(WEB+"/workspace/ai-knowledge",wait_until="domcontentloaded")
                    try:
                        expect(page.get_by_role("heading",name="Approved IFC references (13)",exact=True)).to_be_visible()
                    except AssertionError:
                        print("AI registry browser diagnostics:",urlsplit(page.url).path,page.locator("main").inner_text()[:1200],flush=True)
                        raise
                    for model,score in [("AEC intent classifier","31/32"),("CAD symbol classifier","206/240"),("Experimental AEC language model","6/8"),("Swiss Dwellings polygon model","5954/8140")]:
                        card=page.locator("article").filter(has=page.get_by_role("heading",name=model,exact=True))
                        expect(card).to_contain_text(score)
                        if model in {"Experimental AEC language model","Swiss Dwellings polygon model"}:
                            expect(card).to_contain_text("Runtime not enabled")
                    expect(page.get_by_role("heading",name="Dataset license register",exact=True)).to_be_visible()
                    note("AI evidence frontend reads trained model metrics, approved references and offline runtime boundaries")
                    page.goto(WEB+"/workspace/imports",wait_until="domcontentloaded")
                    expect(page.get_by_role("heading",name="Import runtime evidence",exact=True)).to_be_visible()
                    caps=requests.get(API+"/api/v1/files/capabilities",headers=headers,timeout=20)
                    assert caps.status_code==200
                    note("Imports frontend exposes live backend runtime capability evidence")
                    page.goto(WEB+"/workspace/field",wait_until="domcontentloaded")
                    page.get_by_label("Inspection project",exact=True).select_option(pid)
                    page.get_by_label("Inspection title",exact=True).fill("Browser field observation")
                    page.get_by_label("Site location",exact=True).fill("QA Level 1")
                    page.get_by_label("Observation details",exact=True).fill("Synthetic QA observation: access route obstructed.")
                    page.get_by_role("button",name="Save observation",exact=True).click()
                    observation=page.locator("article").filter(has=page.get_by_role("heading",name="Browser field observation",exact=True))
                    expect(observation).to_be_visible()
                    with page.expect_download() as download:
                        page.get_by_role("button",name="Download observed field report PDF",exact=True).click()
                    assert "Browser field observation" in " ".join(p.extract_text() or "" for p in PdfReader(str(download.value.path())).pages)
                    page.reload(wait_until="domcontentloaded")
                    page.get_by_label("Inspection project",exact=True).select_option(pid)
                    expect(observation).to_be_visible()
                    note("Browser saves field observation, downloads parsed PDF and reloads persisted record")
                    if scanner:
                        ids=[]
                        for idx in range(2):
                            drawing=ezdxf.new("R2000")
                            drawing.header["$INSUNITS"]=4
                            drawing.modelspace().add_line((0,0),(1000,0))
                            if idx:
                                drawing.modelspace().add_line((0,0),(0,1000))
                            stream=io.StringIO()
                            drawing.write(stream)
                            response=requests.post(API+"/api/v1/files/import-dxf",headers=headers,data={"job_id":jid},files={"upload":(f"browser-asbuilt-{idx}.dxf",stream.getvalue().encode(),"application/dxf")},timeout=90)
                            assert response.status_code==201,response.status_code
                            ids.append(response.json()["id"])
                        page.goto(WEB+"/workspace/as-built",wait_until="domcontentloaded")
                        page.get_by_label("Comparison project",exact=True).select_option(pid)
                        page.get_by_label("Original DXF",exact=True).select_option(ids[0])
                        page.get_by_label("Revised DXF",exact=True).select_option(ids[1])
                        page.get_by_role("button",name="Compare and save",exact=True).click()
                        expect(page.get_by_role("heading",name="Geometry comparison evidence",exact=True)).to_be_visible()
                        records=requests.get(API+"/api/v1/asbuilt/projects/"+pid+"/comparisons",headers=headers,timeout=20)
                        assert records.status_code==200 and any(row["result"]["added_count"]==1 and row["result"]["removed_count"]==0 for row in records.json())
                        with page.expect_download() as download:
                            page.get_by_role("button",name="Export verified-source PDF",exact=True).click()
                        assert len(PdfReader(str(download.value.path())).pages)>=1
                        note("Browser compares real imported DXF versions, persists expected geometry difference and downloads PDF")
                        page.goto(WEB+"/workspace/exports",wait_until="domcontentloaded")
                        page.get_by_label("Export source project",exact=True).select_option(pid)
                        page.get_by_label("Export source job",exact=True).select_option(jid)
                        page.get_by_label("Export source drawing",exact=True).select_option(ids[0])
                        page.get_by_role("button",name="Queue CAD export",exact=True).click()
                        expect(page.get_by_text("Export queued. It will run when a dedicated export worker is configured and online.",exact=True)).to_be_visible()
                        with page.expect_download() as download:
                            page.get_by_role("button",name="Download filtered history (CSV)",exact=True).click()
                        assert pid in Path(download.value.path()).read_text()
                        note("Browser queues real export and downloads persisted history CSV; dedicated worker execution not claimed")
                    else:
                        note("Browser as-built/imported export: native scanner unavailable","BLOCKED")
                    page.goto(WEB+"/workspace/members",wait_until="domcontentloaded")
                    page.get_by_label("New workspace name",exact=True).fill("Browser collaboration QA")
                    page.get_by_role("button",name="Create workspace",exact=True).click()
                    expect(page.get_by_text("Workspace created.",exact=True)).to_be_visible()
                    expect(page.get_by_role("heading",name="Invite a member",exact=True)).to_be_visible()
                    page.get_by_placeholder("teammate@email.com").fill(unpaid_email)
                    page.get_by_role("button",name="Send invite",exact=True).click()
                    expect(page.get_by_text(unpaid_email,exact=True)).to_be_visible()
                    expect(page.get_by_role("button",name="Copy invitation code",exact=True)).to_be_visible()
                    page.get_by_role("button",name="Send / retry email",exact=True).click()
                    expect(page.get_by_text("not configured",exact=True)).to_be_visible()
                    note("Browser creates workspace and invitation; provider absence is displayed without claiming delivery")
                    page.goto(WEB+"/workspace/notifications",wait_until="domcontentloaded")
                    expect(page.locator("main").get_by_role("heading",name="Notifications",exact=True)).to_be_visible()
                    unread=page.get_by_role("button",name=__import__("re").compile(r", unread, mark as read$")).first
                    expect(unread).to_be_visible()
                    label=unread.get_attribute("aria-label")
                    unread.click()
                    expect(page.get_by_role("button",name=label.replace(", unread, mark as read",", read, mark as unread"),exact=True).first).to_be_visible()
                    note("Browser notification inbox performs real read transition")
                    page.goto(WEB+"/workspace/activity",wait_until="domcontentloaded")
                    expect(page.locator("main").get_by_role("heading",name="Activity",exact=True)).to_be_visible()
                    page.get_by_label("Filter by project",exact=True).select_option(pid)
                    expect(page.get_by_role("region",name="Activity timeline",exact=True)).to_be_visible()
                    note("Browser filters real persisted activity by project")
                    page.goto(WEB+"/workspace/projects")
                    page.get_by_role("button",name="Archive "+names[0],exact=True).click()
                    page.get_by_role("button",name="Confirm archive",exact=True).click()
                    expect(page.get_by_text(names[0],exact=True)).to_have_count(0)
                    page.goto(WEB+"/workspace/archive")
                    page.get_by_role("button",name="Restore "+names[0],exact=True).click()
                    expect(page.get_by_role("button",name="Restore "+names[0],exact=True)).to_have_count(0)
                    note("Browser archive and restore workflow")
                    # Old projects must remain discoverable beyond the first 20 rows.
                    for index in range(21):
                        r=requests.post(API+"/api/v1/projects/",headers=headers,json={"input_text":f"Pagination QA filler {index:02d}"},timeout=20)
                        assert r.status_code==201
                    page.goto(WEB+"/workspace/projects")
                    expect(page.get_by_role("button",name="Next projects")).to_be_enabled(timeout=60000)
                    page.get_by_role("button",name="Next projects").click()
                    expect(page.get_by_text(names[0],exact=True)).to_be_visible(timeout=60000)
                    page.get_by_placeholder("Search projects...").fill("Browser residential")
                    expect(page.get_by_text(names[0],exact=True)).to_be_visible(timeout=60000)
                    expect(page.get_by_text("Pagination QA filler 00",exact=True)).to_have_count(0)
                    note("Real browser searches older saved projects across pages")
                # New context has no previous browser storage or cookies.
                with browser.new_context() as context:
                    page=login(context,email,password)
                    page.goto(WEB+"/workspace/projects")
                    page.get_by_placeholder("Search projects...").fill("Browser")
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
