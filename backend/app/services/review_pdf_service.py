"""Export the same source-derived DXF viewport and persisted redlines as a PDF."""
from hashlib import sha256
from io import BytesIO
from math import atan2, cos, sin, pi, isfinite
from xml.etree import ElementTree
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from app.services.dxf_preview_service import render_dxf_preview

def build_review_pdf(raw: bytes, record: dict, marks: list[dict]) -> bytes:
    version = int(record.get("version") or 1)
    if len(marks) > 200:
        raise ValueError("Too many redlines for one bounded report")
    for mark in marks:
        if str(mark.get("file_id")) != str(record["id"]) or int(mark["file_version"]) != version:
            raise ValueError("Redline does not match drawing version")
    preview = ElementTree.fromstring(render_dxf_preview(raw))
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4, pageCompression=1)
    width, height = A4
    c.setTitle("Krafzen drawing review")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height-45, "Drawing review")
    c.setFont("Helvetica", 10)
    c.drawString(36, height-65, f"Drawing version {version} | {len(marks)} saved redlines")
    c.drawString(36, height-81, f"File: {record['id']}")
    c.drawString(36, height-97, f"Project: {record['project_id']}")
    c.setFont("Helvetica", 8)
    c.drawString(36, height-111, f"Source SHA-256: {sha256(raw).hexdigest()}")
    side = width-72
    x0, y0 = 36, height-135-side
    scale = side/1000
    def pos(x, y):
        return (x0+float(x)*scale, y0+(1000-float(y))*scale)
    c.setStrokeColor(colors.HexColor("#b8c4cb"))
    c.rect(x0,y0,side,side,stroke=1,fill=0)
    c.setStrokeColor(colors.HexColor("#235361"))
    c.setLineWidth(0.65)
    ns = "{http://www.w3.org/2000/svg}"
    for element in preview.findall(f"{ns}g/*"):
        a=element.attrib
        tag=element.tag.split("}")[-1]
        if tag=="line":
            c.line(*pos(a["x1"],a["y1"]),*pos(a["x2"],a["y2"]))
        elif tag=="circle":
            c.circle(*pos(a["cx"],a["cy"]),float(a["r"])*scale,stroke=1,fill=0)
        elif tag in ("polygon","polyline"):
            vertices=[pos(*point.split(",")) for point in a["points"].split()]
            p=c.beginPath()
            p.moveTo(*vertices[0])
            for v in vertices[1:]: p.lineTo(*v)
            if tag=="polygon": p.close()
            c.drawPath(p)
    for i, mark in enumerate(marks,1):
        values=[float(mark["x"]),float(mark["y"])]
        values.extend(float(mark[k]) if mark.get(k) is not None else values[j] for j,k in enumerate(("x2","y2")))
        if any(not isfinite(v) or not 0<=v<=1 for v in values):
            raise ValueError("Invalid normalized redline coordinate")
        a,b=pos(values[0]*1000,values[1]*1000),pos(values[2]*1000,values[3]*1000)
        ink=colors.HexColor("#64748b" if mark["status"]=="resolved" else "#b91c1c")
        c.setStrokeColor(ink);c.setFillColor(ink);c.setLineWidth(1.3)
        if mark["kind"] in ("line","arrow"):
            c.line(*a,*b)
            if mark["kind"]=="arrow":
                angle=atan2(b[1]-a[1],b[0]-a[0])
                for d in (-pi/6,pi/6):
                    c.line(*b,b[0]-8*cos(angle+d),b[1]-8*sin(angle+d))
        elif mark["kind"] in ("rectangle","highlight"):
            if mark["kind"]=="highlight":
                c.setFillColor(colors.HexColor("#fef3c7"))
                c.saveState();c.setFillAlpha(0.25)
            c.rect(min(a[0],b[0]),min(a[1],b[1]),abs(a[0]-b[0]),abs(a[1]-b[1]),stroke=1,fill=int(mark["kind"]=="highlight"))
            if mark["kind"]=="highlight":c.restoreState()
        else:
            c.circle(*a,5,stroke=1,fill=0)
        c.setFillColor(ink);c.setFont("Helvetica-Bold",8)
        c.drawString(min(a[0]+7,x0+side-18),min(a[1]+5,y0+side-10),str(i))
    c.setFillColor(colors.black);c.setFont("Helvetica",9)
    c.drawString(36,y0-18,"Normalized review preview; not a scaled construction drawing.")
    warning=preview.find(f"{ns}text")
    if warning is not None:
        c.drawString(36,y0-32,warning.text or "Partial preview.")
    c.showPage()
    y=height-42
    def line(text, font="Helvetica", size=10):
        nonlocal y
        for part in simpleSplit(str(text),font,size,width-72):
            if y<48:
                c.showPage();y=height-42
            c.setFont(font,size);c.drawString(36,y,part);y-=size+4
    line("Saved redline register","Helvetica-Bold",16)
    line(f"File: {record['id']} | version {version}")
    line("Redlines are user observations, not engineering certification.")
    for i,mark in enumerate(marks,1):
        y-=8
        line(f"{i}. {mark['kind']} | {mark['severity']} | {mark['status']}","Helvetica-Bold")
        line(f"ID: {mark['id']}")
        line(f"Author: {mark.get('created_by','')} | {mark.get('created_at','')}")
        line(mark["comment"])
    c.save()
    result=stream.getvalue()
    if len(result)>10*1024*1024:
        raise ValueError("Review PDF exceeds export limit")
    return result
