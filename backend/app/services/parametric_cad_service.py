"""Deterministic, unit-explicit architectural room outline to real DXF.

Generates a 2D, dimensioned concept from complete *structured* measurements.
No LLM fills in omitted door/window widths, offsets, code or construction data.
A qualified designer must review before use as construction documentation.
"""
from collections import defaultdict
from io import StringIO
from math import isfinite

import ezdxf


def _positive_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a finite positive measurement in metres")
    return float(value)


def build_room_dxf(
    *, name: str, width_m: float, length_m: float,
    wall_thickness_m: float, openings: list[dict],
) -> tuple[bytes, dict]:
    """Return real DXF bytes and evidence generated from explicitly supplied data.

    Coordinates: origin at southwest exterior wall corner, X east, Y north.
    Width/length are OUTER dimensions, with a single wall thickness for this
    deliberately limited rectangular-room representation.
    """
    width = _positive_number(width_m, "width_m")
    length = _positive_number(length_m, "length_m")
    thickness = _positive_number(wall_thickness_m, "wall_thickness_m")
    if not (1 <= width <= 100 and 1 <= length <= 100):
        raise ValueError("Room exterior dimensions must be between 1 and 100 metres")
    if not (0.05 <= thickness < min(width, length) / 5):
        raise ValueError("Wall thickness must be at least 0.05 m and below 1/5 room span")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError("An explicit room name of 1–80 characters is required")
    if any(ord(ch) < 32 for ch in name):
        raise ValueError("Room name contains unsafe control characters")
    if not isinstance(openings, list) or len(openings) > 20:
        raise ValueError("At most 20 explicitly measured openings are supported")

    groups: dict[str, list[dict]] = defaultdict(list)
    normalized = []
    for index, candidate in enumerate(openings):
        if not isinstance(candidate, dict):
            raise ValueError(f"Opening {index + 1} is malformed")
        side = str(candidate.get("side") or "").lower()
        kind = str(candidate.get("kind") or "").lower()
        if side not in {"north", "south", "east", "west"}:
            raise ValueError(f"Opening {index + 1} has an invalid wall side")
        if kind not in {"door", "window"}:
            raise ValueError(f"Opening {index + 1} must be a door or window")
        offset = _positive_number(candidate.get("offset_m"), "offset_m")
        clearance = _positive_number(candidate.get("clear_width_m"), "clear_width_m")
        span = width if side in {"north", "south"} else length
        if offset < thickness or offset + clearance > span - thickness:
            raise ValueError(f"Opening {index + 1} extends into an exterior wall corner")
        if clearance < 0.3:
            raise ValueError(f"Opening {index + 1} is narrower than supported 0.30 m")
        entry = {
            "kind": kind, "side": side,
            "offset_m": offset, "clear_width_m": clearance,
        }
        normalized.append(entry)
        groups[side].append(entry)

    for side, items in groups.items():
        items.sort(key=lambda item: item["offset_m"])
        for previous, current in zip(items, items[1:]):
            end = previous["offset_m"] + previous["clear_width_m"]
            if current["offset_m"] < end + 0.05:
                raise ValueError(f"Openings on {side} overlap or have insufficient separation")

    document = ezdxf.new("R2010")
    document.header["$INSUNITS"] = 6  # metres, unambiguous physical units
    document.header["$MEASUREMENT"] = 1
    for layer in ("WALLS", "DOORS", "WINDOWS", "JAMBS", "DIMENSIONS", "NOTES"):
        if not document.layers.has_entry(layer):
            document.layers.new(layer)
    model = document.modelspace()

    def xy(side: str, distance: float, inner: bool):
        if side == "south":
            return distance, thickness if inner else 0.0
        if side == "north":
            return distance, length - thickness if inner else length
        if side == "west":
            return thickness if inner else 0.0, distance
        return width - thickness if inner else width, distance

    for side in ("south", "north", "west", "east"):
        span = width if side in ("south", "north") else length
        start = 0.0
        for opening in groups.get(side, []) + [{
            "kind": "end", "offset_m": span, "clear_width_m": 0.0,
        }]:
            gap_start = opening["offset_m"]
            if gap_start > start:
                for inner in (False, True):
                    model.add_line(
                        xy(side, start, inner),
                        xy(side, gap_start, inner),
                        dxfattribs={"layer": "WALLS"},
                    )
            if opening["kind"] != "end":
                gap_end = gap_start + opening["clear_width_m"]
                # Wall returns on each jamb maintain explicit wall thickness.
                for position in (gap_start, gap_end):
                    model.add_line(
                        xy(side, position, False),
                        xy(side, position, True),
                        dxfattribs={"layer": "JAMBS"},
                    )
                centre = (gap_start + gap_end) / 2
                if opening["kind"] == "window":
                    model.add_line(
                        xy(side, gap_start, False),
                        xy(side, gap_end, False),
                        dxfattribs={"layer": "WINDOWS"},
                    )
                    model.add_line(
                        xy(side, gap_start, True),
                        xy(side, gap_end, True),
                        dxfattribs={"layer": "WINDOWS"},
                    )
                else:
                    model.add_line(
                        xy(side, gap_start, True),
                        xy(side, gap_end, True),
                        dxfattribs={"layer": "DOORS"},
                    )
                ax, ay = xy(side, centre, True)
                model.add_text(
                    f"{opening['kind'].upper()} {opening['clear_width_m']:.3f}m",
                    dxfattribs={
                        "height": 0.10,
                        "insert": (ax + 0.05, ay + 0.05),
                        "layer": "NOTES",
                    },
                )
                start = gap_end

    # EZDXF creates real DIMENSION entities with proper generated anonymous
    # blocks, not decorative text purporting to contain dimensions.
    model.add_linear_dim(
        base=(width / 2, -0.75),
        p1=(0, 0), p2=(width, 0), angle=0,
        text=f"{width:.3f} m", dimstyle="EZDXF",
        dxfattribs={"layer": "DIMENSIONS"},
        override={"dimtxt": 0.13, "dimasz": 0.09},
    ).render()
    model.add_linear_dim(
        base=(-0.75, length / 2),
        p1=(0, 0), p2=(0, length), angle=90,
        text=f"{length:.3f} m", dimstyle="EZDXF",
        dxfattribs={"layer": "DIMENSIONS"},
        override={"dimtxt": 0.13, "dimasz": 0.09},
    ).render()
    model.add_text(
        name.strip(),
        dxfattribs={
            "height": 0.16, "insert": (thickness + 0.2, length / 2),
            "layer": "NOTES",
        },
    )
    out = StringIO()
    document.write(out)
    content = out.getvalue().encode("utf-8")
    if len(content) < 100 or not content.startswith(b"  0"):
        raise RuntimeError("Generated parametric DXF is invalid")
    return content, {
        "type": "cad", "generation_method": "parametric_room_v1",
        "room_name": name.strip(), "exterior_width_m": width,
        "exterior_length_m": length, "wall_thickness_m": thickness,
        "interior_clear_width_m": width - 2 * thickness,
        "interior_clear_length_m": length - 2 * thickness,
        "interior_clear_area_m2": round(
            (width - 2 * thickness) * (length - 2 * thickness), 6
        ),
        "openings": normalized,
        "units": "metres", "autocad_insunits": 6,
        "engineering_accuracy_verified": False,
        "requires_professional_review": True,
        "limitations": (
            "Single rectangular 2D concept with uniformly thick parallel walls. "
            "No structural calculation, door swing or accessibility certification, "
            "wall assembly, site survey, MEP or fire-safety check."
        ),
    }
