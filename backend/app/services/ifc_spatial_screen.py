"""Deterministic broad-phase screening of actual IFC tessellated products.

This detects axis-aligned bounding-box (AABB) intersections in the coordinate
space of uploaded IFC geometry; it DOES NOT confirm hard clashes, clearances
or physical construction discrepancies. Both models must already be aligned.
"""
from math import isfinite

MAX_ELEMENTS = 500
MAX_CANDIDATES = 200
MIN_OVERLAP = 1e-5


def _checked_bounds(element: dict) -> tuple[list[float], list[float]]:
    if not isinstance(element, dict):
        raise ValueError("Malformed tessellated IFC element")
    vertices = element.get("vertices")
    faces = element.get("triangles")
    if (
        not isinstance(vertices, list) or not isinstance(faces, list)
        or not vertices or not faces or len(vertices) % 3 or len(faces) % 3
        or len(vertices) > 135_000 or len(faces) > 75_000
    ):
        raise ValueError("IFC element is missing valid tessellation arrays")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float))
        or not isfinite(v) or abs(v) > 1e9
        for v in vertices
    ):
        raise ValueError("IFC element contains invalid coordinates")
    size = len(vertices) // 3
    if any(type(f) is not int or f < 0 or f >= size for f in faces):
        raise ValueError("IFC element contains invalid triangle indices")
    mins = [min(vertices[k::3]) for k in range(3)]
    maxs = [max(vertices[k::3]) for k in range(3)]
    return mins, maxs


def _screen_elements(mesh: dict) -> list[dict]:
    if (
        not isinstance(mesh, dict) or mesh.get("type") != "ifc_true_mesh"
        or mesh.get("geometry_source") != "actual_ifc_product_tessellation"
    ):
        raise ValueError("Only real, source-derived IFC triangle meshes can be screened")
    elements = mesh.get("elements")
    if not isinstance(elements, list) or not 1 <= len(elements) <= MAX_ELEMENTS:
        raise ValueError("IFC mesh has no valid bounded element set")
    inspected = []
    for element in elements:
        bounds = _checked_bounds(element)
        inspected.append({
            "guid": str(element.get("guid") or "")[:32],
            "name": str(element.get("name") or "")[:120],
            "ifc_type": str(element.get("ifc_type") or "")[:64],
            "min": bounds[0],
            "max": bounds[1],
        })
    return inspected


def screen_ifc_mesh_overlap(
    primary: dict,
    secondary: dict,
    *,
    primary_file_id: str,
    secondary_file_id: str,
    primary_sha256: str,
    secondary_sha256: str,
) -> dict:
    """Produce bounded, raw-coordinate *potential* overlaps across 2 IFC files.

    No fabricated element, auto-registration, collision proof or model federation
    claim. Never report a clear result as evidence of zero building clashes.
    """
    a = _screen_elements(primary)
    b = _screen_elements(secondary)
    candidates: list[dict] = []
    total = 0
    for element_a in a:
        for element_b in b:
            lows = [
                max(element_a["min"][axis], element_b["min"][axis])
                for axis in range(3)
            ]
            highs = [
                min(element_a["max"][axis], element_b["max"][axis])
                for axis in range(3)
            ]
            dimensions = [hi - lo for lo, hi in zip(lows, highs)]
            # AABB face touching is not a volumetric overlap. Ignore
            # dimensionally degenerate boxes and superficial shared faces.
            if not all(depth > MIN_OVERLAP for depth in dimensions):
                continue
            total += 1
            if len(candidates) < MAX_CANDIDATES:
                candidates.append({
                    "source": {
                        "file_id": primary_file_id,
                        "guid": element_a["guid"],
                        "ifc_type": element_a["ifc_type"],
                        "name": element_a["name"],
                    },
                    "target": {
                        "file_id": secondary_file_id,
                        "guid": element_b["guid"],
                        "ifc_type": element_b["ifc_type"],
                        "name": element_b["name"],
                    },
                    "overlap_min": [round(v, 5) for v in lows],
                    "overlap_max": [round(v, 5) for v in highs],
                    "overlap_extents_model_coordinates": [
                        round(v, 5) for v in dimensions
                    ],
                    "classification": "potential_spatial_overlap_unverified",
                })
    partial = bool(primary.get("partial_model") or secondary.get("partial_model"))
    return {
        "method": "ifc_world_coordinate_aabb_broad_phase_v1",
        "geometry_source": "actual_ifc_product_tessellation",
        "source_files": [
            {
                "file_id": primary_file_id, "sha256": primary_sha256,
                "ifc_schema": primary.get("schema"),
                "rendered_element_count": len(a),
                "partial_model": bool(primary.get("partial_model")),
            },
            {
                "file_id": secondary_file_id, "sha256": secondary_sha256,
                "ifc_schema": secondary.get("schema"),
                "rendered_element_count": len(b),
                "partial_model": bool(secondary.get("partial_model")),
            },
        ],
        "coordinate_alignment": "user_asserted_same_origin_axes_and_scale_not_verified",
        "candidate_count": total,
        "candidates": candidates,
        "candidate_list_truncated": total > len(candidates),
        "analysis_partial": partial,
        "hard_clashes_confirmed": 0,
        "full_federation_or_clearance_checks_performed": False,
        "requires_professional_review": True,
        "limitations": (
            "Intersections of 3D axis-aligned bounds are ONLY potential "
            "overlaps. True surfaces may not intersect. IFC sources must "
            "share verified coordinate systems and scale; user assertion is "
            "not geometric registration. Tessellation may omit IFC products "
            "or exceed limits. No narrow-phase solid intersection, signed "
            "clearance, issue assignment, model federation, or code approval."
        ),
    }
