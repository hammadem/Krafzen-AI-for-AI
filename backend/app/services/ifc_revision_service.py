"""Compare real world-space IFC mesh evidence by stable GlobalId.

This is not semantic revision reconciliation or a model federation tool.
Changes in triangulation can change the fingerprint even for equivalent solids.
"""
import hashlib
import json
from collections import Counter


def _fingerprint(element: dict) -> str:
    vertices = element["vertices"]
    faces = element["triangles"]
    points = [tuple(vertices[i:i+3]) for i in range(0, len(vertices), 3)]
    # Invariant under face order, vertex index order and triangle winding;
    # deliberately not invariant under a different tessellation of a surface.
    triangles = sorted(tuple(sorted(points[faces[i+j]] for j in range(3)))
                       for i in range(0, len(faces), 3))
    return hashlib.sha256(json.dumps(triangles, separators=(",", ":")).encode()).hexdigest()


def compare_ifc_mesh_revisions(before: dict, after: dict) -> dict:
    for model in (before, after):
        if model.get("type") != "ifc_true_mesh" or not model.get("elements"):
            raise ValueError("Real IFC tessellation is required")
    def index(model):
        counts = Counter(str(x.get("guid") or "") for x in model["elements"])
        duplicates = sorted(g for g, n in counts.items() if g and n > 1)
        items = {str(x["guid"]): x for x in model["elements"]
                 if x.get("guid") and counts[str(x["guid"])] == 1}
        return items, set(duplicates), counts.get("", 0)
    a, da, ma = index(before)
    b, db, mb = index(after)
    blocked = da | db
    for key in blocked:
        a.pop(key, None)
        b.pop(key, None)
    # Absence from a partial mesh is not proof of an added/removed IFC product.
    partial_a = bool(before.get("partial_model")) or bool(da or ma)
    partial_b = bool(after.get("partial_model")) or bool(db or mb)
    rows = []
    def add(guid, status, element):
        rows.append({"guid": guid, "change": status, "ifc_type": element["ifc_type"],
                     "name": element["name"]})
    for guid in sorted(a.keys() - b.keys()):
        add(guid, "not_observed_in_revised" if partial_b else "removed_from_mesh", a[guid])
    for guid in sorted(b.keys() - a.keys()):
        add(guid, "not_observed_in_original" if partial_a else "added_to_mesh", b[guid])
    unchanged = 0
    for guid in sorted(a.keys() & b.keys()):
        if _fingerprint(a[guid]) != _fingerprint(b[guid]):
            add(guid, "tessellation_or_placement_changed", b[guid])
        elif (a[guid]["ifc_type"], a[guid]["name"]) != (b[guid]["ifc_type"], b[guid]["name"]):
            add(guid, "name_or_type_changed", b[guid])
        else:
            unchanged += 1
    return {
        "method": "ifc_guid_mesh_revision_v1",
        "candidate_count": len(rows),
        "candidates": [],
        "analysis_partial": partial_a or partial_b,
        "candidate_list_truncated": False,
        "hard_clashes_confirmed": 0,
        "coordinate_alignment": "user_asserted_same_origin_axes_and_scale_not_verified",
        "revision": {
            "counts": dict(sorted(Counter(r["change"] for r in rows).items())),
            "unchanged_mesh_and_identity_count": unchanged,
            "ambiguous_duplicate_guids": sorted(blocked),
            "missing_guid_count": ma + mb,
            "changes": rows[:500],
            "changes_truncated": len(rows) > 500,
        },
        "requires_professional_review": True,
        "limitations": "Comparison of bounded world-space tessellated representations by stable GlobalId. Added/removed refers to observed mesh products, not verified construction. Different mesh triangulation can produce a change without a physical change. Unobserved products in partial geometry remain uncertain. Properties, relationships, nonrepresented products and full IFC semantic equivalence are not compared.",
    }
