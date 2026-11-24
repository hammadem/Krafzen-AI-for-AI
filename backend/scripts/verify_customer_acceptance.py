"""Real isolated acceptance checkpoint, never connected to a customer cloud DB.

No Stripe requests, fake scanner, mocked API, or production entitlement writes.
The paid fixture is created only inside a disposable local Supabase stack.
"""
import io
import json
import os
import secrets
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import ezdxf
import psycopg2
import requests


def local_url(value, scheme):
    p = urlsplit(value or "")
    if p.scheme != scheme or p.hostname not in {"127.0.0.1", "localhost"} or p.query or p.fragment:
        raise RuntimeError("Acceptance requires a local disposable stack")
    return value


def configure():
    info = {}
    for line in Path(os.environ["LOCAL_SUPABASE_STATUS_FILE"]).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip().strip('"').strip("'")
    api = local_url(info.get("API_URL") or info.get("PROJECT_URL") or info.get("SUPABASE_URL"), "http")
    db_url = local_url(info["DB_URL"], "postgresql")
    role = info.get("SERVICE_ROLE_KEY") or info.get("SECRET_KEY")
    anon = info.get("ANON_KEY") or info.get("PUBLISHABLE_KEY")
    assert role and anon
    os.environ.update(SUPABASE_URL=api.rstrip("/"), SUPABASE_PROJECT_ID="local-ci",
                      SUPABASE_SERVICE_ROLE_KEY=role, SUPABASE_ANON_KEY=anon,
                      SUPABASE_JWT_SECRET="", ENVIRONMENT="test",
                      KRAFZEN_EXPORT_WORKER_ENABLED="0", GEMINI_API_KEY="",
                      STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="")
    return api.rstrip("/"), db_url, role, anon


def main():
    api, dsn, role, anon = configure()
    from fastapi.testclient import TestClient
    from app.main import app
    from tests.unit.test_ifc_native_coordination import create_real_solid
    from pypdf import PdfReader

    evidence = []
    def note(case, step, status="PASS"):
        evidence.append(dict(case=case, step=step, status=status))
        print(f"{status}: {case} | {step}", flush=True)

    def user():
        email = "qa-" + secrets.token_hex(8) + "@example.com"
        password = secrets.token_urlsafe(32)
        r = requests.post(api + "/auth/v1/admin/users",
                          headers={"apikey": role, "Authorization": "Bearer " + role},
                          json={"email": email, "password": password, "email_confirm": True}, timeout=20)
        assert r.status_code in (200, 201), f"Auth account creation HTTP {r.status_code}"
        uid = r.json()["id"]
        r = requests.post(api + "/auth/v1/token?grant_type=password",
                          headers={"apikey": anon}, json={"email": email, "password": password}, timeout=20)
        assert r.status_code == 200, f"Auth sign-in HTTP {r.status_code}"
        return uid, {"Authorization": "Bearer " + r.json()["access_token"]}

    def paid_fixture(uid):
        # A local-only test prerequisite, NOT verified payment or Stripe acceptance.
        with psycopg2.connect(dsn) as con, con.cursor() as cur:
            cur.execute("""UPDATE public.user_subscriptions SET plan_name='starter',
                plan_tier='starter', billing_cycle='monthly', subscription_status='active',
                stripe_subscription_id=%s, plan_requests_total=50, plan_requests_remaining=50,
                plan_requests_reset_date=%s WHERE user_id=%s""",
                        ("qa-fixture-" + uid, datetime.now(timezone.utc) + timedelta(days=30), uid))
            assert cur.rowcount == 1, "Missing local signup subscription"

    def check(resp, status=200):
        assert resp.status_code == status, f"{resp.request.method} {resp.request.url.path}: HTTP {resp.status_code}, expected {status}"
        return resp

    def pdf(resp):
        check(resp)
        assert resp.content.startswith(b"%PDF-") and len(PdfReader(io.BytesIO(resp.content)).pages) >= 1

    def drawing(dx=0, dy=0, revised=False):
        doc = ezdxf.new("R2010")
        doc.header["$INSUNITS"] = 4
        m = doc.modelspace()
        m.add_line((dx, dy), (dx+5000, dy))
        m.add_circle((dx+1000, dy+1000), 200)
        if revised:
            m.add_line((dx+2000, dy+1000), (dx+2000, dy+3000))
        out = io.StringIO()
        doc.write(out)
        return out.getvalue().encode()

    def scanner_available():
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp)/"clean.txt"
                p.write_text("Isolated acceptance clean input.")
                return subprocess.run(["clamscan","--no-summary",str(p)],
                    capture_output=True, timeout=60).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    with TestClient(app) as client:
        base = "/api/v1"
        uid, headers = user()
        other_uid, other = user()
        with psycopg2.connect(dsn) as con, con.cursor() as cur:
            cur.execute("SELECT trial_requests_remaining, plan_requests_remaining FROM public.user_subscriptions WHERE user_id=%s", (uid,))
            assert cur.fetchone() == (0, 0)
        check(client.post(base+"/projects/", json={"input_text":"unauthenticated"}),401)
        check(client.post(base+"/projects/", headers=headers, json={"input_text":"unpaid"}),402)
        note("E", "Real Auth account + login; signup credits zero; unpaid and anonymous access rejected")
        note("E", "Provider checkout, verified payment activation, invoice, actual usage billing", "DEFERRED")
        paid_fixture(uid)
        paid_fixture(other_uid)

        def project(name):
            p = check(client.post(base+"/projects/", headers=headers,json={"input_text":name}),201).json()["id"]
            j = check(client.post(base+"/jobs/",headers=headers,json={"project_id":p}),201).json()["id"]
            return p,j

        def upload(job, filename, data):
            kind = filename.rsplit(".",1)[-1]
            return check(client.post(base+"/files/import-"+kind,headers=headers,
                data={"job_id":job},files={"upload":(filename,data,"application/octet-stream")}),201).json()["id"]

        p,j=project("Residential QA fixture")
        note("A","Create project and job")
        forbidden=client.get(base+"/projects/"+p,headers=other)
        assert forbidden.status_code in (403,404)
        note("A","Different paid account cannot open project")
        cad=check(client.post(base+"/cad/rooms",headers=headers,json={
            "project_id":p,"job_id":j,"room_name":"QA room","exterior_width_m":5,
            "exterior_length_m":4,"wall_thickness_m":0.2}),201).json()
        assert cad["geometry"]["autocad_insunits"]==6
        fid=cad["file"]["id"]
        file=check(client.get(base+"/files/"+fid,headers=headers)).json()
        assert file["id"]==fid
        signed=check(client.get(base+"/files/"+fid+"/signed-url",headers=headers)).json()
        assert signed.get("signed_url") or signed.get("signedUrl") or signed.get("url")
        note("A","Real dimensioned CAD generation persisted in private storage; signed link")
        preview=check(client.get(base+"/reviews/files/"+fid+"/preview.svg",headers=headers))
        assert b"<svg" in preview.content
        note("A","Actual CAD preview SVG")
        red=check(client.post(base+"/reviews/files/"+fid+"/redlines",headers=headers,json={
            "kind":"comment","x":0.25,"y":0.25,"comment":"Review fixture","severity":"info"}),201).json()["id"]
        assert any(x["id"]==red for x in check(client.get(base+"/reviews/files/"+fid+"/redlines",headers=headers)).json())
        check(client.patch(base+"/reviews/redlines/"+red,headers=headers,json={"status":"resolved"}))
        note("A","Saved redline, reopened and resolved")
        assessment=check(client.post(base+"/compliance/ada-measurements",headers=headers,json={
            "project_id":p,"source_file_id":fid,
            "jurisdiction":{"state":"Test State","municipality":"Test City",
              "project_address":"123 QA Test Street","occupancy":"Residential","building_type":"Residential",
              "standard_edition":"2010_ADA","ada_applicability_confirmed":True},
            "measurements":{"door_kind":"manual_swinging","door_clear_width_in":32,
              "doorway_depth_in":10,"door_measured_at_90_degrees":True,
              "accessible_route_clear_width_in":36,"route_exception_applies":False,
              "ramp_rise_in":6,"ramp_horizontal_run_in":72,"new_construction":True,
              "ramp_alteration_exception_applies":False}}),201).json()
        assert assessment["result"]["complete_code_compliance_determined"] is False
        assert assessment["result"]["counts"]["pass"]==3
        assert any(x["id"]==assessment["id"] for x in check(client.get(base+"/compliance/projects/"+p+"/ada-measurements",headers=headers)).json())
        note("A","ADA measurement screening and persisted findings (test applicability only)")
        # Additional compliance routes become available after their separate PR is merged.
        paths=client.get("/openapi.json").json()["paths"]
        if base+"/compliance/assessments/{assessment_id}/report.pdf" in paths:
            pdf(client.get(base+"/compliance/assessments/"+assessment["id"]+"/report.pdf",headers=headers))
            note("A","Saved compliance PDF download and parse")
        else:
            note("A","Saved compliance PDF route not yet in this revision","BLOCKED")
        check(client.post(base+"/projects/"+p+"/archive",headers=headers))
        check(client.post(base+"/projects/"+p+"/restore",headers=headers))
        assert check(client.get(base+"/projects/"+p,headers=headers)).json()["id"]==p
        note("A","Project archive, restore and reopen")
        note("A","Full browser drawing dimensions and queued CAD/DWG export","NOT_RUN")

        if scanner_available():
            a=upload(j,"original.dxf",drawing())
            b=upload(j,"revised.dxf",drawing(100,-50,True))
            note("A/D","Actual scanned original and revised DXF imports")
            result=check(client.post(base+"/asbuilt/compare",headers=headers,json={
              "project_id":p,"original_file_id":a,"revised_file_id":b,
              "alignment":{"original":{"x":0,"y":0},"revised":{"x":100,"y":-50},
                "same_reference_point_confirmed":True}}),201).json()
            assert result["result"]["added_count"]==1 and result["result"]["unchanged_count"]==2
            assert result["result"]["removed_count"]==0
            assert any(x["id"]==result["id"] for x in check(client.get(base+"/asbuilt/projects/"+p+"/comparisons",headers=headers)).json())
            pdf(client.get(base+"/asbuilt/comparisons/"+result["id"]+"/report.pdf",headers=headers))
            note("A/D","Aligned comparison, expected geometry difference, saved history and parsed PDF")
            bp,bj=project("BIM QA fixture")
            with tempfile.TemporaryDirectory() as tmp:
                first,_=create_real_solid(Path(tmp)/"a.ifc")
                second,_=create_real_solid(Path(tmp)/"b.ifc",offset=(0.2,0.02,0.5),dims=(0.8,0.08,1))
            a=upload(bj,"a.ifc",first)
            b=upload(bj,"b.ifc",second)
            note("C","Real IFC scanned import and second model")
            mesh=check(client.get(base+"/bim/files/"+a+"/mesh",headers=headers)).json()
            assert mesh["mesh"]["elements"]
            note("C","Actual source-derived 3D geometry")
            clash=check(client.post(base+"/bim/projects/"+bp+"/spatial-screens",headers=headers,json={
                "primary_file_id":a,"secondary_file_id":b,"same_origin_axes_and_scale_confirmed":True,
                "mode":"native_coordination","clearance_m":0.05}),201).json()
            assert clash["result"]["hard_clashes_confirmed"]>=1
            assert any(x["id"]==clash["id"] for x in check(client.get(base+"/bim/projects/"+bp+"/spatial-screens",headers=headers)).json())
            note("C","Native IFC hard clash and persisted result")
        else:
            # A real scanner failure is evidence of a blocker, not permission to bypass it.
            response=client.post(base+"/files/import-dxf",headers=headers,data={"job_id":j},
                files={"upload":("original.dxf",drawing(),"application/dxf")})
            check(response,503)
            note("A/C/D","Imports and dependent comparison/coordination: real scanner unavailable; import fails closed","BLOCKED")
        note("B","Commercial multidisciplinary assignment, adopted-code full review, member audit","NOT_RUN")
        note("C","Browser interaction, properties/quantities, IFC revision comparison, comprehensive model validation","NOT_RUN")
        note("D","Full review and export workflow","NOT_RUN")

    Path(os.environ.get("ACCEPTANCE_RESULT_FILE","customer-acceptance.json")).write_text(
        json.dumps({"scope":"isolated backend API checkpoints; not full customer acceptance",
                    "payment":"deferred; local QA fixture only","checks":evidence},indent=2))


if __name__=="__main__":
    main()
