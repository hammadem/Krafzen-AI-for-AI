"""Bounded native IfcOpenShell IFC coordination, operating on source models.

The geometric engine measures intersections and separation in metres. These
are engineering review findings, not authority approval. The caller verifies
ownership, scanned source provenance, and explicit coordinate alignment.
"""
import json
import math
import sys
from collections import Counter

MAX_PRODUCTS_PER_MODEL = 200
MAX_FINDINGS = 300
MAX_TRIANGLES_PER_MODEL = 100_000
HARD_TOLERANCE_M = 0.002


def _guid(element):
    return str(element.GlobalId or "")


def _point(raw):
    point = [float(x) for x in raw]
    if len(point) != 3 or not all(math.isfinite(x) and abs(x) <= 1e9 for x in point):
        raise ValueError("Invalid geometry-engine result")
    return point


def coordinate_ifc_models(first, second, clearance_m=0.05):
    import ifcopenshell
    import ifcopenshell.geom

    if not math.isfinite(clearance_m) or not 0.001 <= clearance_m <= 1:
        raise ValueError("Clearance must be between 1 mm and 1 m")
    models = [ifcopenshell.open(path) for path in (first, second)]
    if any(not (m.schema in ("IFC2X3", "IFC4") or m.schema.startswith("IFC4X3"))
           for m in models):
        raise ValueError("Unsupported IFC schema")
    # Keep both source model instances alive for the entire native tree lifetime.
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    tree = ifcopenshell.geom.tree(backend="opencascade.trianglebvh")
    groups, summaries, issues = [], [], []
    memberships = []
    for index, model in enumerate(models):
        products = [p for p in model.by_type("IfcElement")
                    if getattr(p, "Representation", None)
                    and not p.is_a("IfcFeatureElementSubtraction")]
        if not products:
            raise ValueError("Model contains no represented physical IFC elements")
        counts = Counter(_guid(p) for p in products)
        invalid = {guid for guid, count in counts.items() if not guid or count > 1}
        for guid in sorted(invalid)[:MAX_FINDINGS]:
            issues.append({"classification": "missing_or_duplicate_identifier",
                           "model_index": index, "guid": guid,
                           "count": counts[guid], "severity": "review"})
        chosen = [p for p in products if _guid(p) not in invalid][:MAX_PRODUCTS_PER_MODEL]
        if not chosen:
            raise ValueError("No uniquely identified represented elements")
        # Validate tessellations before placing elements in the native BVH.
        # This gives explicit counts for unprocessable or budget-excluded shapes.
        usable, triangles = [], 0
        for element in chosen:
            try:
                shape = ifcopenshell.geom.create_shape(settings, element)
                n = len(shape.geometry.faces) // 3
                if n <= 0 or triangles + n > MAX_TRIANGLES_PER_MODEL:
                    continue
                triangles += n
                usable.append(element)
            except Exception:
                continue
        if not usable:
            raise ValueError("No valid geometric elements")
        # Single thread keeps native memory/CPU demand bounded on free hosting.
        iterator = ifcopenshell.geom.iterator(settings, model, 1, include=usable)
        tree.add_iterator(iterator)
        # Verify that the BVH actually contains each indexed element. A failed
        # iterator must not result in an apparent clash-free model.
        indexed = []
        for element in usable:
            try:
                if any(p == element for p in tree.select_box(element)):
                    indexed.append(element)
            except Exception:
                continue
        if not indexed:
            raise ValueError("Native geometry index is empty")
        groups.append(indexed)
        memberships.append({_guid(e): e for e in indexed})
        summaries.append({
            "model_index": index, "schema": model.schema,
            "represented_element_count": len(products),
            "indexed_element_count": len(indexed),
            "excluded_element_count": len(products) - len(indexed),
            "partial": len(indexed) != len(products),
        })

    # A repeated GlobalId across sources is evidence of a shared/duplicated
    # model identity, not proof that two physical objects are duplicates.
    common = sorted(set(memberships[0]) & set(memberships[1]))
    for guid in common[:MAX_FINDINGS]:
        issues.append({"classification": "shared_global_id_across_sources",
                       "guid": guid, "severity": "review"})

    def _ref(raw, model_index):
        guid = str(raw.get_argument(0))
        element = memberships[model_index].get(guid)
        if element is None:
            raise ValueError("Clash could not be attributed to its source model")
        return {"model_index": model_index, "guid": guid,
                "ifc_type": element.is_a(), "name": str(element.Name or "")[:120]}

    findings = []
    counts = Counter()
    hard_pairs = set()
    for result in tree.clash_intersection_many(
        groups[0], groups[1], tolerance=HARD_TOLERANCE_M, check_all=True
    ):
        kind = ("protrusion", "pierce", "collision", "clearance")[result.clash_type]
        a, b = _ref(result.a, 0), _ref(result.b, 1)
        distance = float(result.distance)
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("Invalid intersection distance")
        # Non-manifold surface contact is not a confirmed solid intersection.
        classification = "hard_clash" if kind in ("protrusion", "pierce") and distance >= HARD_TOLERANCE_M else "surface_conflict"
        hard_pairs.add((a["guid"], b["guid"]))
        counts[classification] += 1
        if len(findings) < MAX_FINDINGS:
            findings.append({"classification": classification, "engine_type": kind,
                             "severity": "high" if classification == "hard_clash" else "review",
                             "source": a, "target": b, "distance_m": distance,
                             "location_a_m": _point(result.p1),
                             "location_b_m": _point(result.p2)})
    for result in tree.clash_clearance_many(
        groups[0], groups[1], clearance=clearance_m, check_all=True
    ):
        a, b = _ref(result.a, 0), _ref(result.b, 1)
        if (a["guid"], b["guid"]) in hard_pairs:
            continue
        distance = float(result.distance)
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("Invalid clearance distance")
        if distance >= clearance_m:
            continue
        counts["clearance_conflict"] += 1
        if len(findings) < MAX_FINDINGS:
            findings.append({"classification": "clearance_conflict",
                             "engine_type": "clearance", "severity": "review",
                             "source": a, "target": b, "distance_m": distance,
                             "required_clearance_m": clearance_m,
                             "location_a_m": _point(result.p1),
                             "location_b_m": _point(result.p2)})
    total = sum(counts.values())
    return {
        "method": "ifcopenshell_native_intersection_clearance_v1",
        "geometry_engine": "IfcOpenShell BVH",
        "coordinate_alignment": "user_asserted_same_origin_axes_and_scale_not_verified",
        "length_unit": "m", "intersection_tolerance_m": HARD_TOLERANCE_M,
        "clearance_threshold_m": clearance_m,
        "source_models": summaries,
        "analysis_partial": any(s["partial"] for s in summaries),
        "candidate_count": total, "candidates": findings,
        "candidate_list_truncated": total > len(findings),
        "hard_clashes_confirmed": counts["hard_clash"],
        "surface_conflict_count": counts["surface_conflict"],
        "clearance_conflict_count": counts["clearance_conflict"],
        "shared_global_id_count": len(common),
        "identity_findings": issues[:MAX_FINDINGS],
        "requires_professional_review": True,
        "limitations": (
            "Native geometry intersection and clearance checks on represented, "
            "indexed IFC elements only. User-asserted alignment is not "
            "independently verified. Touching or non-manifold surfaces require "
            "review. Clearance is user-selected, not a code requirement. "
            "Severity is coordination priority, not a safety certification. "
            "Connectivity, intentional penetrations, duplicate physical objects, "
            "and omitted geometry require independent review. No findings does "
            "not prove clash-free construction."
        ),
    }


def main():
    if len(sys.argv) != 4:
        return 2
    try:
        try:
            import resource
            cap = 1536 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
        except (ImportError, OSError, ValueError):
            pass
        report = coordinate_ifc_models(sys.argv[1], sys.argv[2], float(sys.argv[3]))
        print(json.dumps(report, allow_nan=False, separators=(",", ":")))
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    sys.exit(main())
