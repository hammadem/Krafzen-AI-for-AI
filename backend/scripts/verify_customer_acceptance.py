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
    def save_evidence():
        Path(os.environ.get("ACCEPTANCE_RESULT_FILE","customer-acceptance.json")).write_text(json.dumps({"scope":"isolated backend API checkpoints; not full customer acceptance","payment":"deferred; local QA fixture only","checks":evidence},indent=2))
    def note(case, step, status="PASS"):
        evidence.append(dict(case=case, step=step, status=status))
        print(f"{status}: {case} | {step}", flush=True)
        save_evidence()

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
            balance = cur.fetchone()
            assert balance == (0, 0), f"Expected zero signup balance; subscription row={balance is not None}"
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
        session_path = base + "/chat/session"
        linked = check(client.post(session_path,headers=headers,json={"project_id":p})).json()
        assert linked["project_id"] == p
        assert check(client.post(session_path,headers=headers,json={"project_id":p})).json()["id"] == linked["id"]
        check(client.post(session_path,headers=other,json={"project_id":p}),403)
        check(client.get(base+"/chat/history/"+linked["id"],headers=other),403)
        assert check(client.get(base+"/chat/history/"+linked["id"],headers=headers)).json()["messages"] == []
        check(client.get(base+"/chat/history/"+linked["id"],headers=headers,params={"limit":101}),422)
        note("Chat","Existing project links to persistent owner-scoped design session; reuse and tenant isolation verified without paid AI calls")
        register = check(client.get(base+"/chat/reference-register",headers=headers)).json()
        assert register["dataset_count"] >= 6
        ref_answer = check(client.post(base+"/chat/reference",headers=headers,json={"session_id":linked["id"],"question":"IFC wall opening window"})).json()
        assert ref_answer["mode"] == "local_approved_reference_retrieval" and ref_answer["references"]
        assert "CC BY 4.0" in ref_answer["validated_response"] and "buildingSMART" in ref_answer["validated_response"]
        assert ref_answer["image_url"] == ""
        check(client.post(base+"/chat/reference",headers=other,json={"session_id":linked["id"],"question":"IFC walls"}),404)
        saved = check(client.get(base+"/chat/history/"+linked["id"],headers=headers)).json()["messages"]
        assert any(row["id"] == ref_answer["message_id"] and "buildingSMART" in row["content"] for row in saved)
        note("Knowledge","Approved IFC source index, licensed references, saved chat response and tenant isolation verified without paid AI")
        check(client.post(base+"/projects/",headers=headers,json={"input_text":"   "}),422)
        check(client.post(base+"/projects/",headers=headers,json={"input_text":""}),422)
        check(client.post(base+"/projects/",headers=headers,json={"input_text":"x"*20001}),422)
        own_search=check(client.get(base+"/projects/",headers=headers,params={"q":"Residential QA"})).json()
        assert {row["id"] for row in own_search} == {p}
        assert check(client.get(base+"/projects/",headers=other,params={"q":"Residential QA"})).json() == []
        check(client.delete(base+"/projects/"+p,headers=other),403)
        note("Projects","Reject blank/oversized inputs, search only owned rows and deny cross-account deletion")
        metadata = {"title":"Campus, Phase (2)", "description":"Detailed commercial design", "project_type":"commercial", "lifecycle_stage":"in_review"}
        detailed = check(client.post(base+"/projects/",headers=headers,json={**metadata,"input_text":"Campus structured project"}),201).json()
        detailed_id = detailed["id"]
        assert all(detailed[key] == value for key,value in metadata.items())
        check(client.patch(base+"/projects/"+detailed_id,headers=other,json={"title":"Unauthorized"}),403)
        changed = check(client.patch(base+"/projects/"+detailed_id,headers=headers,json={"title":"Campus, Phase (3)","lifecycle_stage":"completed"})).json()
        assert changed["title"] == "Campus, Phase (3)" and changed["lifecycle_stage"] == "completed"
        assert check(client.get(base+"/projects/"+detailed_id,headers=headers)).json()["description"] == metadata["description"]
        assert {row["id"] for row in check(client.get(base+"/projects/",headers=headers,params={"q":"Campus, Phase (3)","project_type":"commercial","lifecycle_stage":"completed"})).json()} == {detailed_id}
        assert check(client.get(base+"/projects/",headers=other,params={"q":"Campus, Phase (3)"})).json() == []
        check(client.patch(base+"/projects/"+detailed_id,headers=headers,json={"title":"   "}),422)
        check(client.patch(base+"/projects/"+detailed_id,headers=headers,json={"lifecycle_stage":"fake"}),422)
        check(client.patch(base+"/projects/"+detailed_id,headers=headers,json={"dxf_url":"https://fake.example/dxf"}),422)
        check(client.post(base+"/projects/"+detailed_id+"/archive",headers=headers))
        check(client.patch(base+"/projects/"+detailed_id,headers=headers,json={"title":"Archived edit"}),409)
        check(client.post(base+"/projects/"+detailed_id+"/restore",headers=headers))
        assert check(client.get(base+"/projects/"+detailed_id,headers=headers)).json()["title"] == "Campus, Phase (3)"
        check(client.delete(base+"/projects/"+detailed_id,headers=headers))
        note("Projects","Structured project metadata persists, filters correctly, and remains protected by owner and archive rules")
        check(client.post(base+"/workspaces/",headers=headers,json={"name":"   "}),422)
        created = check(client.post(base+"/workspaces/",headers=headers,json={"name":"Isolated collaboration QA"}),201).json()
        ws = created["id"]
        assert created["owner_id"] == uid
        assert any(row["id"] == ws for row in check(client.get(base+"/workspaces/",headers=headers)).json())
        assert all(row["id"] != ws for row in check(client.get(base+"/workspaces/",headers=other)).json())
        with psycopg2.connect(dsn) as con, con.cursor() as cur:
            cur.execute("SELECT email FROM auth.users WHERE id=%s", (other_uid,))
            invite_email = cur.fetchone()[0]
        workspace = base + "/workspaces/" + ws
        check(client.get(workspace, headers=other),403)
        invite = check(client.post(workspace+"/invites",headers=headers,
            json={"email":invite_email,"role":"viewer"}),201).json()
        check(client.post(workspace+"/invites",headers=headers,
            json={"email":invite_email,"role":"viewer"}),409)
        revoke_path = workspace+"/invites/"+invite["id"]+"/revoke"
        check(client.patch(revoke_path,headers=other),403)
        check(client.patch(revoke_path,headers=headers))
        reissued = check(client.post(workspace+"/invites",headers=headers,
            json={"email":invite_email,"role":"viewer"}),201).json()
        assert reissued["id"] == invite["id"] and reissued["token"] != invite["token"]
        assert check(client.get(base+"/workspaces/invites/validate",headers=other,
            params={"token":invite["token"]})).json()["valid"] is False
        check(client.post(base+"/workspaces/invites/accept",headers=other,
            json={"token":reissued["token"]}))
        assert check(client.get(workspace,headers=other)).json()["id"] == ws
        assert any(row["id"] == ws for row in check(client.get(base+"/workspaces/",headers=other)).json())
        members = check(client.get(workspace+"/members",headers=headers)).json()["members"]
        assert any(row["user_id"] == other_uid and row["role"] == "viewer" for row in members)
        member_path = workspace+"/members/"+other_uid
        check(client.patch(member_path,headers=other,json={"role":"admin"}),403)
        assert check(client.patch(member_path,headers=headers,json={"role":"member"})).json()["role"] == "member"
        check(client.delete(member_path,headers=headers))
        check(client.get(workspace,headers=other),403)
        workspace_events = check(client.get(base+"/activity/workspace/"+ws,headers=headers)).json()
        assert {"team.member_invited","team.member_joined","permissions.access_granted","permissions.access_revoked"} <= {e["action"] for e in workspace_events}
        assert check(client.get(base+"/activity/workspace/"+ws,headers=other)).json() == []
        note("B/Members","Real API workspace creation, catalog, invite, revoke, reissue, accept, role change, removal and scoped audit history")

        prefs_path=base+"/notifications/preferences"
        defaults=check(client.get(prefs_path,headers=headers)).json()
        assert all(defaults.values())
        assert check(client.put(prefs_path,headers=headers,json={**defaults,"field":False})).json()["field"] is False
        assert check(client.get(prefs_path,headers=other)).json()["field"] is True
        inspection = check(client.post(base+"/field/inspections",headers=headers,json={
            "project_id":p,"title":"QA observation","description":"Recorded site observation",
            "discipline":"architecture","severity":"medium"}),201).json()
        inspection_id = inspection["id"]
        notes_path = base+"/field/inspections/"+inspection_id+"/notes"
        note_data = check(client.post(notes_path,headers=headers,json={"kind":"corrective_action","body":"Recheck measured clearance","due_date":"2027-01-15"}),201).json()
        check(client.post(notes_path,headers=headers,json={"kind":"comment","body":"Awaiting site confirmation"}),201)
        check(client.post(notes_path,headers=headers,json={"kind":"comment","body":"Invalid due date","due_date":"2027-01-15"}),422)
        assert any(row["id"]==note_data["id"] and row["due_date"]=="2027-01-15" for row in check(client.get(notes_path,headers=headers)).json())
        assert client.get(notes_path,headers=other).status_code in (403,404)
        assert client.post(notes_path,headers=other,json={"kind":"comment","body":"Forbidden"}).status_code in (403,404)
        note("Field","Persisted comments and due-dated corrective action, tenant isolation verified")
        status_path = base+"/field/inspections/"+inspection_id+"/status"
        check(client.patch(status_path,headers=headers,json={"status":"verified"}),409)
        denied = client.patch(status_path,headers=other,json={"status":"resolved"})
        assert denied.status_code in (403,404)
        check(client.patch(status_path,headers=headers,json={"status":"in_progress"}))
        check(client.patch(status_path,headers=headers,json={"status":"resolved"}))
        assert check(client.patch(status_path,headers=headers,json={"status":"verified"})).json()["status"] == "verified"
        records = check(client.get(base+"/field/projects/"+p+"/inspections",headers=headers)).json()
        assert any(row["id"] == inspection_id and row["status"] == "verified" for row in records)
        denied = client.get(base+"/field/projects/"+p+"/report.pdf",headers=other)
        assert denied.status_code in (403,404)
        report = client.get(base+"/field/projects/"+p+"/report.pdf",headers=headers)
        pdf(report)
        assert "QA observation" in "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(report.content)).pages)
        note("Field","Real observation persistence, status transitions, authorization and parsed PDF report")
        assert not any(row["type"]=="field_update" for row in check(client.get(base+"/notifications/",headers=headers)).json())
        check(client.put(prefs_path,headers=headers,json=defaults))
        check(client.patch(status_path,headers=headers,json={"status":"open"}))
        assert any(row["type"]=="field_update" and row["metadata"]["source_id"]==inspection_id for row in check(client.get(base+"/notifications/",headers=headers)).json())
        check(client.post(base+"/notifications/read-all",headers=headers))
        assert check(client.get(base+"/notifications/",headers=headers,params={"unread_only":True})).json()==[]
        note("Notifications","Persistent category preference suppresses real field events, reenable restores delivery, mark all read scoped to owner")
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
        # Verify browser REST writes cannot replace trusted storage metadata.
        browser = requests.patch(api + "/rest/v1/files?id=eq." + fid,
            headers={"apikey": anon, **headers, "Prefer": "return=representation"},
            json={"path": "untrusted/replacement.dxf"}, timeout=20)
        assert browser.status_code in (401, 403), f"Browser metadata mutation HTTP {browser.status_code}"
        note("A","Direct browser metadata modification rejected")
        events=check(client.get(base+"/dashboard/activity",headers=headers,params={"project_id":p})).json()["events"]
        assert any(e.get("action") == "file.uploaded" and e.get("entity_id") == fid for e in events)
        assert any(e.get("action") == "revision.created" and e.get("entity_id") == fid for e in events)
        assert check(client.get(base+"/dashboard/activity",headers=other,params={"project_id":p})).json()["events"] == []
        note("A","Real canonical file and revision audit events; cross-account isolation")
        note("A","Real dimensioned CAD generation persisted in private storage; signed link")
        # Check actual signed storage bytes and dimensional DXF entities.
        signed_path = signed.get("signed_url") or signed.get("signedUrl") or signed.get("url")
        signed_parsed = urlsplit(signed_path)
        assert signed_parsed.hostname in {"127.0.0.1", "localhost"}
        downloaded = requests.get(signed_path, timeout=20)
        assert downloaded.status_code == 200
        doc = ezdxf.read(io.StringIO(downloaded.content.decode("utf-8")))
        assert doc.header["$INSUNITS"] == 6
        assert len(doc.modelspace().query("DIMENSION")) >= 2
        note("A","Downloaded private DXF parses with real dimension entities and metre units")

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
            inbox_path = base + "/dashboard/notifications"
            unread = check(client.get(inbox_path,headers=headers,params={"unread_only":True,"limit":1})).json()
            assert unread["total"] >= 2 and len(unread["notifications"]) == 1
            notification = unread["notifications"][0]
            assert notification["title"] == "Import completed" and notification["read"] is False
            second = check(client.get(inbox_path,headers=headers,params={"unread_only":True,"limit":1,"offset":1})).json()
            assert second["notifications"][0]["id"] != notification["id"]
            notification_id = notification["id"]
            check(client.patch(inbox_path+"/"+notification_id+"/read",headers=other),404)
            assert all(row["id"] != notification_id for row in check(client.get(inbox_path,headers=other)).json()["notifications"])
            check(client.patch(inbox_path+"/"+notification_id+"/read",headers=headers))
            refreshed = check(client.get(inbox_path,headers=headers)).json()["notifications"]
            assert any(row["id"] == notification_id and row["read"] for row in refreshed)
            assert all(row["id"] != notification_id for row in check(client.get(inbox_path,headers=headers,params={"unread_only":True})).json()["notifications"])
            direct = check(client.get(base+"/notifications/",headers=headers)).json()
            assert any(row["id"] == notification_id and row["is_read"] for row in direct)
            note("Notifications","Real scanned import emits a persisted inbox notification; pagination, read-state persistence and tenant isolation verified")
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
            query_path = base+"/bim/files/"+a+"/query"
            answer = check(client.post(query_path,headers=headers,json={"mode":"count","entity_class":"IfcWall"})).json()
            assert answer["result"]["match_count"] == 1 and answer["source_sha256"]
            elements = check(client.post(query_path,headers=headers,json={"mode":"elements","entity_class":"IfcWall"})).json()["result"]["elements"]
            assert len(elements) == 1 and elements[0]["name"] == "Measured 2m wall"
            assert check(client.post(query_path,headers=headers,json={"mode":"properties","element_guid":elements[0]["guid"]})).json()["result"]["element"]["guid"] == elements[0]["guid"]
            assert client.post(query_path,headers=other,json={"mode":"count"}).status_code in (403,404)
            note("C","Source-bound IFC count, element inventory and property lookup; cross-account access denied")
            mesh=check(client.get(base+"/bim/files/"+a+"/mesh",headers=headers)).json()
            assert mesh["mesh"]["elements"]
            note("C","Actual source-derived 3D geometry")
            clash=check(client.post(base+"/bim/projects/"+bp+"/spatial-screens",headers=headers,json={
                "primary_file_id":a,"secondary_file_id":b,"same_origin_axes_and_scale_confirmed":True,
                "mode":"native_coordination","clearance_m":0.05}),201).json()
            assert clash["result"]["hard_clashes_confirmed"]>=1
            assert any(x["id"]==clash["id"] for x in check(client.get(base+"/bim/projects/"+bp+"/spatial-screens",headers=headers)).json())
            note("C","Native IFC hard clash and persisted result")
            validation_path=base+"/bim/files/"+a+"/validations"
            diagnostic=check(client.post(validation_path,headers=headers),201).json()
            assert diagnostic["result"]["geometry_checked_count"]==1
            assert diagnostic["result"]["geometry_failed_count"]==0
            assert diagnostic["result"]["complete_model_validity_determined"] is False
            assert any(x["id"]==diagnostic["id"] for x in check(client.get(validation_path,headers=headers)).json())
            assert client.get(validation_path,headers=other).status_code in (403,404)
            note("C","Real native IFC validation evidence, history and cross-account isolation")
            revision=check(client.post(base+"/bim/projects/"+bp+"/spatial-screens",headers=headers,json={
                "primary_file_id":a,"secondary_file_id":b,"same_origin_axes_and_scale_confirmed":True,
                "mode":"revision_comparison"}),201).json()
            assert revision["result"]["method"]=="ifc_guid_mesh_revision_v1"
            assert revision["result"]["revision"]["counts"]=={"added_to_mesh":1,"removed_from_mesh":1}
            note("C","Actual bounded IFC revision comparison and saved evidence")
        else:
            # A real scanner failure is evidence of a blocker, not permission to bypass it.
            response=client.post(base+"/files/import-dxf",headers=headers,data={"job_id":j},
                files={"upload":("original.dxf",drawing(),"application/dxf")})
            check(response,503)
            note("A/C/D","Imports and dependent comparison/coordination: real scanner unavailable; import fails closed","BLOCKED")
        if base+"/compliance/building-code-measurements" in paths:
            from tests.unit.test_building_code_measurement_rules import CONTEXT, MEASURES
            commercial,cj=project("Commercial QA fixture")
            commercial_cad=check(client.post(base+"/cad/rooms",headers=headers,json={
                "project_id":commercial,"job_id":cj,"room_name":"Commercial test source","exterior_width_m":10,
                "exterior_length_m":8,"wall_thickness_m":0.2}),201).json()["file"]["id"]
            code=check(client.post(base+"/compliance/building-code-measurements",headers=headers,json={
                "project_id":commercial,"source_file_id":commercial_cad,
                "jurisdiction":CONTEXT,"measurements":MEASURES}),201).json()
            assert code["result"]["counts"]=={"pass":7,"fail":1,"unknown":0}
            assert code["result"]["complete_code_compliance_determined"] is False
            pdf(client.get(base+"/compliance/assessments/"+code["id"]+"/report.pdf",headers=headers))
            note("B","Commercial project; real saved IBC/NFPA numeric screening and report using declared QA measurements")
        else:
            note("B","IBC/NFPA assessment route not in tested revision","BLOCKED")
        note("B","Full multidisciplinary project assignment and adopted-code comprehensive review","NOT_RUN")
        note("C","Browser interaction, full quantities and comprehensive model validity","NOT_RUN")
        note("D","Full review and export workflow","NOT_RUN")

    Path(os.environ.get("ACCEPTANCE_RESULT_FILE","customer-acceptance.json")).write_text(
        json.dumps({"scope":"isolated backend API checkpoints; not full customer acceptance",
                    "payment":"deferred; local QA fixture only","checks":evidence},indent=2))


if __name__=="__main__":
    main()
