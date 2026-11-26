"""Conservative deterministic DXF review; never a code-compliance result."""
from collections import defaultdict
from hashlib import sha256
from io import StringIO
from math import isfinite

import ezdxf

from app.services.dxf_preview_service import MAX_BYTES, MAX_ENTITIES


def inspect_dxf_review(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES or b"\x00" in raw[:128]:
        raise ValueError("Unsupported DXF source")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    try:
        doc = ezdxf.read(StringIO(text))
    except Exception as exc:
        raise ValueError("Invalid DXF source") from exc
    groups = defaultdict(list)
    points = []
    findings = []
    checked = skipped = dimensions = notes = 0
    count = 0

    def coordinates(value):
        result = tuple(float(v) for v in value)
        if not all(isfinite(v) and abs(v) < 1e10 for v in result):
            raise ValueError("Invalid or excessive DXF coordinates")
        return result

    for count, entity in enumerate(doc.modelspace(), 1):
        if count > MAX_ENTITIES:
            raise ValueError("DXF review exceeds 10,000 modelspace entities")
        kind = entity.dxftype()
        if kind == "DIMENSION":
            dimensions += 1
        if kind in ("TEXT", "MTEXT"):
            notes += 1
        if kind == "LINE":
            start, end = coordinates(entity.dxf.start), coordinates(entity.dxf.end)
            points.extend((start[:2], end[:2]))
            checked += 1
            layer = str(entity.dxf.layer)
            handle = str(entity.dxf.handle)
            middle = tuple((a+b)/2 for a,b in zip(start,end))
            # Full 3D coordinates and same layer; reversed endpoints count.
            if start == end:
                findings.append({"kind":"zero_length_line", "layer":layer, "handles":[handle],
                                 "source_point":middle, "severity":"medium",
                                 "message":"Line has identical start and end coordinates.",
                                 "recommendation":"Review whether this zero-length line is intentional."})
            else:
                groups[(layer, tuple(sorted((start,end))))].append(handle)
        elif kind == "LWPOLYLINE":
            vertices = list(entity.get_points("xyb"))
            if len(vertices) >= 2 and not any(abs(float(p[2])) > 1e-12 for p in vertices):
                points.extend(coordinates(p[:2]) for p in vertices)
            skipped += 1
        elif kind == "CIRCLE":
            x,y,_ = coordinates(entity.dxf.center)
            radius = float(entity.dxf.radius)
            if not isfinite(radius) or radius <= 0:
                raise ValueError("Invalid circle radius")
            points.extend((coordinates((x-radius,y-radius)),coordinates((x+radius,y+radius))))
            skipped += 1
        else:
            skipped += 1
    for (layer, endpoints), handles in groups.items():
        if len(handles) > 1:
            a,b = endpoints
            findings.append({"kind":"coincident_line", "layer":layer, "handles":handles[:50],
                             "occurrence_count":len(handles), "source_point":tuple((x+y)/2 for x,y in zip(a,b)),
                             "severity":"low", "message":"Multiple lines on the same layer have identical 3D endpoints.",
                             "recommendation":"Confirm whether the overlapping entities are intentional before deleting any."})
    if not points:
        raise ValueError("No supported preview geometry for source-linked review")
    xs,ys=zip(*points)
    cx,cy=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2
    scale=900/max(max(xs)-min(xs),max(ys)-min(ys),1e-6)
    for item in findings:
        x,y,_=item["source_point"]
        item["x"]=round((500+(x-cx)*scale)/1000,6)
        item["y"]=round((500-(y-cy)*scale)/1000,6)
    return {"method":"dxf_exact_line_screen_v1","source_sha256":sha256(raw).hexdigest(),
            "modelspace_entity_count":count,"checked_line_count":checked,"unchecked_entity_count":skipped,
            "dimension_entity_count":dimensions,"text_entity_count":notes,
            "finding_count":len(findings),"findings":findings[:100],"truncated":len(findings)>100,
            "limitations":"Exact same-layer LINE endpoints and zero-length LINE checks only. Dimension and text counts are observations, not missing-dimension or annotation findings. No tolerance, other geometry, layer semantics, design intent or code compliance determination."}
