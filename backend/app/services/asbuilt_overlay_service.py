"""Conservative, source-derived, bounded DXF comparison preview primitives.

Only 2D LINE, unbulged LWPOLYLINE and CIRCLE are displayed. No
approximated 3D/ARC geometry or invented field evidence is rendered.
"""
from collections import Counter
from math import isfinite

MAX_PREVIEW_ENTITIES = 120


def preview_differences(
    unchanged: Counter, added: Counter, removed: Counter
) -> dict:
    groups: dict[str, list[dict]] = {}
    unavailable: set[str] = set()
    truncated = False
    coords: list[tuple[float, float]] = []

    def take(counter: Counter) -> list[dict]:
        nonlocal truncated
        output: list[dict] = []
        for signature, count in sorted(counter.items(), key=lambda item: str(item[0])):
            if len(output) >= MAX_PREVIEW_ENTITIES:
                truncated = True
                break
            kind, layer = signature[:2]
            primitive = None
            if kind == "LINE":
                a, b = signature[2:]
                primitive = {
                    "type": "line", "layer": layer, "count": count,
                    "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1],
                }
                coords.extend(((a[0], a[1]), (b[0], b[1])))
            elif kind == "CIRCLE":
                center, radius = signature[2:]
                if isfinite(radius) and radius > 0:
                    primitive = {
                        "type": "circle", "layer": layer, "count": count,
                        "cx": center[0], "cy": center[1], "radius": radius,
                    }
                    coords.extend((
                        (center[0] - radius, center[1] - radius),
                        (center[0] + radius, center[1] + radius),
                    ))
            elif kind == "LWPOLYLINE":
                points = signature[4]
                if (
                    len(points) >= 2
                    and all(len(point) == 5 and
                            abs(point[2]) < 1e-8 and
                            abs(point[3]) < 1e-8 and
                            abs(point[4]) < 1e-8 for point in points)
                ):
                    vertices = [[p[0], p[1]] for p in points]
                    primitive = {
                        "type": "polyline", "layer": layer,
                        "count": count, "closed": bool(signature[2]),
                        "points": vertices,
                    }
                    coords.extend((p[0], p[1]) for p in points)
            if primitive is None:
                unavailable.add(str(kind))
            else:
                output.append(primitive)
        return output

    for category, counter in (
        ("unchanged", unchanged), ("removed", removed), ("added", added)
    ):
        groups[category] = take(counter)

    if not coords:
        return {
            "groups": groups, "bounds": None, "truncated": truncated,
            "omitted_entity_types": sorted(unavailable),
            "source": "real_dxf_modelspace_signatures",
            "coverage": "2d_preview_supported_primitives_only",
        }

    xs, ys = zip(*coords)
    if not all(isfinite(value) and abs(value) <= 1e9 for value in xs + ys):
        raise ValueError("Unrenderable DXF coordinates")
    return {
        "groups": groups,
        "bounds": {
            "min_x": min(xs), "min_y": min(ys),
            "max_x": max(xs), "max_y": max(ys),
        },
        "truncated": truncated,
        "omitted_entity_types": sorted(unavailable),
        "source": "real_dxf_modelspace_signatures",
        "coverage": "2d_preview_supported_primitives_only",
    }
