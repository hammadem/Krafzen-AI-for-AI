"""Bounded, deterministic SVG preview of supported DXF modelspace entities.

Only directly rendered LINE, straight LWPOLYLINE, and CIRCLE entities are shown.
Unsupported drawings are explicitly partial; never misrepresent hidden geometry.
All SVG markup is generated from numeric coordinates, not untrusted DXF text.
"""
from io import StringIO
from math import isfinite
from xml.sax.saxutils import escape

import ezdxf

MAX_BYTES = 25 * 1024 * 1024
MAX_ENTITIES = 10000


def render_dxf_preview(raw: bytes) -> str:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ValueError("DXF must be a nonempty file of at most 25 MB")
    if b"\x00" in raw[:128]:
        raise ValueError("Binary DXF preview is not supported")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    try:
        drawing = ezdxf.read(StringIO(text))
    except Exception as exc:
        raise ValueError("DXF preview could not be parsed") from exc

    shapes = []
    points = []
    skipped = 0
    for number, entity in enumerate(drawing.modelspace(), 1):
        if number > MAX_ENTITIES:
            raise ValueError("DXF preview exceeds 10,000 entities")
        kind = entity.dxftype()
        if kind == "LINE":
            a, b = entity.dxf.start, entity.dxf.end
            p1, p2 = (float(a.x), float(a.y)), (float(b.x), float(b.y))
            shapes.append(("line", p1, p2))
            points.extend((p1, p2))
        elif kind == "LWPOLYLINE":
            vertices = list(entity.get_points("xyb"))
            # Bulges are curved arcs. Never draw them as inaccurate straight lines.
            if len(vertices) < 2 or any(abs(float(p[2])) > 1e-12 for p in vertices):
                skipped += 1
                continue
            poly = tuple((float(p[0]), float(p[1])) for p in vertices)
            shapes.append(("poly", poly, bool(entity.closed)))
            points.extend(poly)
        elif kind == "CIRCLE":
            center = entity.dxf.center
            x, y, radius = float(center.x), float(center.y), float(entity.dxf.radius)
            if radius <= 0:
                raise ValueError("Invalid circle radius in source DXF")
            shapes.append(("circle", (x, y), radius))
            points.extend(((x-radius, y-radius), (x+radius, y+radius)))
        else:
            skipped += 1

    if not points:
        raise ValueError("No supported visible LINE, straight polyline or CIRCLE geometry")
    if not all(isfinite(v) and abs(v) < 1e10 for p in points for v in p):
        raise ValueError("DXF preview coordinates are invalid or excessive")

    xs, ys = zip(*points)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    extent = max(max(xs)-min(xs), max(ys)-min(ys), 1e-6)
    scale = 900 / extent

    def tx(x):
        return round(500 + (x-cx)*scale, 3)

    def ty(y):
        return round(500 - (y-cy)*scale, 3)

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">',
        '<rect width="1000" height="1000" fill="#081522"/>',
        '<g fill="none" stroke="#66e4cf" stroke-width="2" stroke-linejoin="round">',
    ]
    for shape in shapes:
        if shape[0] == "line":
            _, a, b = shape
            svg.append(
                f'<line x1="{tx(a[0])}" y1="{ty(a[1])}" '
                f'x2="{tx(b[0])}" y2="{ty(b[1])}"/>'
            )
        elif shape[0] == "poly":
            _, poly, closed = shape
            values = " ".join(f"{tx(x)},{ty(y)}" for x, y in poly)
            tag = "polygon" if closed else "polyline"
            svg.append(f'<{tag} points="{values}"/>')
        elif shape[0] == "circle":
            _, center, radius = shape
            svg.append(
                f'<circle cx="{tx(center[0])}" cy="{ty(center[1])}" r="{round(radius*scale, 3)}"/>'
            )
    svg.append("</g>")
    if skipped:
        svg.append(
            f'<text x="18" y="980" fill="#fbbf24" font-size="16">'
            f'{skipped} unsupported entities omitted — partial DXF preview</text>'
        )
    svg.append("</svg>")
    return "".join(svg)
