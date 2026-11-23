"""Deterministic unit-aware comparison of two real DXF drawings.

Conservative geometry diff, not a claim of physical as-built verification,
drawing registration, or complete CAD/entity semantics. Uploaded source files
have already passed mandatory malware scanning at the import boundary.
"""
from collections import Counter
from hashlib import sha256
from io import StringIO
from math import isfinite
from typing import Any

from app.services.asbuilt_overlay_service import preview_differences

import ezdxf

MAX_DXF_BYTES = 25 * 1024 * 1024
MAX_ENTITIES = 50000
SUPPORTED = {"LINE", "LWPOLYLINE", "CIRCLE", "ARC"}


def _round(value: Any) -> float:
    number = float(value)
    if not isfinite(number) or abs(number) > 1e9:
        raise ValueError("DXF modelspace contains invalid or nonfinite coordinates")
    return round(number, 6)


def _translation(alignment: dict | None) -> tuple[tuple[float, float], dict | None]:
    if alignment is None:
        return (0.0, 0.0), None
    if not isinstance(alignment, dict) or alignment.get("same_reference_point_confirmed") is not True:
        raise ValueError("Explicit common reference point confirmation is required")
    points = {}
    for label in ("original", "revised"):
        point = alignment.get(label)
        if not isinstance(point, dict):
            raise ValueError("Original and revised drawing reference points are required")
        pair = []
        for key in ("x", "y"):
            value = point.get(key)
            if isinstance(value, bool) or not isinstance(value, (float, int)):
                raise ValueError("Registration reference coordinates must be numbers")
            if not isfinite(value) or abs(value) > 1e8:
                raise ValueError("Registration reference coordinates exceed bounds")
            pair.append(float(value))
        points[label] = pair
    delta = (
        _round(points["original"][0] - points["revised"][0]),
        _round(points["original"][1] - points["revised"][1]),
    )
    if any(abs(part) > 1e7 for part in delta):
        raise ValueError("Registration translation exceeds supported range")
    return delta, {
        "kind": "manual_2d_reference_translation",
        "original_anchor_xy": points["original"],
        "revised_anchor_xy": points["revised"],
        "revised_translation_xy": list(delta),
        "user_confirmed_same_reference_point": True,
        "automatically_verified": False,
        "rotation_or_scale_performed": False,
    }


def _translated_signature(signature: tuple, dx: float, dy: float) -> tuple:
    if dx == dy == 0:
        return signature
    kind, layer = signature[:2]
    def shift(point: tuple) -> tuple:
        return (_round(point[0] + dx), _round(point[1] + dy), point[2])
    if kind == "LINE":
        return (kind, layer, *sorted((shift(signature[2]), shift(signature[3]))))
    if kind in ("CIRCLE", "ARC"):
        return (kind, layer, shift(signature[2]), *signature[3:])
    if kind == "LWPOLYLINE":
        points = tuple(
            (_round(p[0] + dx), _round(p[1] + dy), *p[2:])
            for p in signature[4]
        )
        return (kind, layer, signature[2], signature[3], points)
    raise ValueError("Unsupported registration entity")



def _xy3(point: Any) -> tuple[float, float, float]:
    return tuple(_round(v) for v in (point.x, point.y, point.z))


def _signature(entity: Any) -> tuple:
    kind = entity.dxftype()
    layer = str(entity.dxf.layer)
    if kind == "LINE":
        endpoints = sorted((_xy3(entity.dxf.start), _xy3(entity.dxf.end)))
        return (kind, layer, *endpoints)
    if kind == "CIRCLE":
        return (kind, layer, _xy3(entity.dxf.center), _round(entity.dxf.radius))
    if kind == "ARC":
        return (
            kind, layer, _xy3(entity.dxf.center), _round(entity.dxf.radius),
            _round(entity.dxf.start_angle) % 360,
            _round(entity.dxf.end_angle) % 360,
        )
    if kind == "LWPOLYLINE":
        pts = tuple(tuple(_round(v) for v in row) for row in entity.get_points("xyseb"))
        return (
            kind, layer, bool(entity.closed),
            _round(entity.dxf.get("elevation", 0)),
            pts,
        )
    raise ValueError("Unsupported geometry type")


def _read_dxf(raw: bytes, *, translation: tuple[float, float] = (0.0, 0.0)) -> tuple[Counter, Counter, int]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_DXF_BYTES:
        raise ValueError("DXF input must be nonempty and at most 25 MB")
    if b"\x00" in raw[:128]:
        raise ValueError("Binary DXF files are not supported by this comparator")
    # Imported DXF files are validated already; support common ASCII encodings
    # while making malformed stream failures explicit.
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    try:
        doc = ezdxf.read(StringIO(text))
    except Exception as exc:
        raise ValueError("Invalid or unreadable ASCII DXF") from exc
    units = int(doc.header.get("$INSUNITS", 0))
    if units == 0:
        raise ValueError("Both drawings must declare explicit INSUNITS for a dimensional comparison")
    geometry: Counter = Counter()
    unsupported: Counter = Counter()
    count = 0
    for entity in doc.modelspace():
        count += 1
        if count > MAX_ENTITIES:
            raise ValueError("Drawing exceeds the 50,000-entity comparison limit")
        kind = entity.dxftype()
        if kind not in SUPPORTED:
            unsupported[kind] += 1
            continue
        try:
            geometry[_translated_signature(_signature(entity), *translation)] += 1
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Malformed supported DXF entity") from exc
    if not count:
        raise ValueError("DXF has no modelspace entities")
    return geometry, unsupported, units


def _serialize_signature(signature: tuple) -> dict[str, Any]:
    return {"entity": signature[0], "layer": signature[1], "geometry": str(signature[2:])[:400]}


def compare_dxf_bytes(original: bytes, revised: bytes, *, alignment: dict | None = None) -> dict[str, Any]:
    """Compare geometric modelspace entities using common declared units/coordinates.

    An entity moved or changed is reported as one removal plus one addition.
    Never claim alignment to field surveys, full structural equivalence, or
    dimensional accuracy of the underlying drawing.
    """
    translation, reference = _translation(alignment)
    old, old_unsupported, old_units = _read_dxf(original)
    new, new_unsupported, new_units = _read_dxf(revised, translation=translation)
    if old_units != new_units:
        raise ValueError("Drawings have different INSUNITS; register and convert units before comparing")

    added = new - old
    removed = old - new
    unchanged = old & new
    overlay = preview_differences(unchanged, added, removed)
    def samples(counter: Counter) -> list[dict[str, Any]]:
        results = []
        for signature, quantity in sorted(counter.items(), key=lambda item: str(item[0]))[:100]:
            results.append({**_serialize_signature(signature), "count": quantity})
        return results

    return {
        "method": "manual_translation_entity_diff_v2" if reference else "exact_coordinate_entity_diff_v1",
        "alignment": reference,
        "preview": overlay,
        "source_hash_sha256": sha256(original).hexdigest(),
        "revised_hash_sha256": sha256(revised).hexdigest(),
        "insunits": old_units,
        "original_supported_count": sum(old.values()),
        "revised_supported_count": sum(new.values()),
        "unchanged_count": sum(unchanged.values()),
        "added_count": sum(added.values()),
        "removed_count": sum(removed.values()),
        "added_samples": samples(added),
        "removed_samples": samples(removed),
        "unsupported_original": dict(sorted(old_unsupported.items())),
        "unsupported_revised": dict(sorted(new_unsupported.items())),
        "comparison_complete": not (old_unsupported or new_unsupported),
        "requires_professional_review": True,
        "limitations": (
            "Only exact modelspace coordinates after an explicitly entered 2D "
            "translation (if provided). Anchor points are asserted by the user, "
            "NOT independently verified; no rotation, scaling, automatic model "
            "registration, survey alignment, complex solids/blocks, or physical "
            "construction confirmation. Moved/edited entities appear as "
            "additions and removals. The visual preview omits unsupported curves."

        ),
    }
