"""Deterministic unit-aware comparison of two real DXF drawings.

Conservative geometry diff, not a claim of physical as-built verification,
drawing registration, or complete CAD/entity semantics. Uploaded source files
have already passed mandatory malware scanning at the import boundary.
"""
from collections import Counter
from hashlib import sha256
from io import StringIO
from typing import Any

import ezdxf

MAX_DXF_BYTES = 25 * 1024 * 1024
MAX_ENTITIES = 50000
SUPPORTED = {"LINE", "LWPOLYLINE", "CIRCLE", "ARC"}


def _round(value: Any) -> float:
    return round(float(value), 6)


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


def _read_dxf(raw: bytes) -> tuple[Counter, Counter, int]:
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
            geometry[_signature(entity)] += 1
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Malformed supported DXF entity") from exc
    if not count:
        raise ValueError("DXF has no modelspace entities")
    return geometry, unsupported, units


def _serialize_signature(signature: tuple) -> dict[str, Any]:
    return {"entity": signature[0], "layer": signature[1], "geometry": str(signature[2:])[:400]}


def compare_dxf_bytes(original: bytes, revised: bytes) -> dict[str, Any]:
    """Compare geometric modelspace entities using common declared units/coordinates.

    An entity moved or changed is reported as one removal plus one addition.
    Never claim alignment to field surveys, full structural equivalence, or
    dimensional accuracy of the underlying drawing.
    """
    old, old_unsupported, old_units = _read_dxf(original)
    new, new_unsupported, new_units = _read_dxf(revised)
    if old_units != new_units:
        raise ValueError("Drawings have different INSUNITS; register and convert units before comparing")

    added = new - old
    removed = old - new
    unchanged = old & new
    def samples(counter: Counter) -> list[dict[str, Any]]:
        results = []
        for signature, quantity in sorted(counter.items(), key=lambda item: str(item[0]))[:100]:
            results.append({**_serialize_signature(signature), "count": quantity})
        return results

    return {
        "method": "exact_coordinate_entity_diff_v1",
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
            "Exact modelspace coordinates only: no automatic registration, "
            "field survey validation, complex solids/blocks, or dimensional certification. "
            "Moved/edited entities appear as additions and removals."
        ),
    }
