"""True IFC mesh tessellation using IfcOpenShell native geometry.

This module only emits triangles from ACTUAL product representations in the
uploaded IFC file; never example blocks or inferred boxes from element counts.
Executed in a memory/CPU bounded child process by bim_geometry_routes.
"""
import json
import math
import sys
from pathlib import Path

MAX_PRODUCTS = 500
MAX_VERTICES = 45000
MAX_TRIANGLES = 25000
MAX_JSON_BYTES = 8 * 1024 * 1024


def extract_ifc_mesh(path: str) -> dict:
    import ifcopenshell
    import ifcopenshell.geom

    model = ifcopenshell.open(path)
    schema = str(model.schema).upper()
    if schema not in ("IFC2X3", "IFC4") and not schema.startswith("IFC4X3"):
        raise ValueError("Unsupported IFC model schema")

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    products = [
        item for item in model.by_type("IfcProduct")
        if getattr(item, "Representation", None)
    ]
    if not products:
        raise ValueError("No products with geometry representations in this model")

    elements = []
    failures = 0
    total_vertices = 0
    total_triangles = 0
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3

    for product in products[:MAX_PRODUCTS]:
        try:
            result = ifcopenshell.geom.create_shape(settings, product)
            raw_vertices = list(result.geometry.verts)
            raw_faces = list(result.geometry.faces)
            if len(raw_vertices) % 3 or len(raw_faces) % 3:
                failures += 1
                continue
            vertex_count = len(raw_vertices) // 3
            face_count = len(raw_faces) // 3
            if vertex_count == 0 or face_count == 0:
                failures += 1
                continue
            if (total_vertices + vertex_count > MAX_VERTICES or
                total_triangles + face_count > MAX_TRIANGLES):
                break
            if not all(
                math.isfinite(value) and abs(value) <= 1e9
                for value in raw_vertices
            ):
                failures += 1
                continue
            if any(not isinstance(index, int) or index < 0 or index >= vertex_count
                   for index in raw_faces):
                failures += 1
                continue

            vertices = [round(float(x), 5) for x in raw_vertices]
            triangles = [int(x) for x in raw_faces]
            for axis in range(3):
                values = vertices[axis::3]
                mins[axis] = min(mins[axis], *values)
                maxs[axis] = max(maxs[axis], *values)
            elements.append({
                "guid": str(product.GlobalId or "")[:32],
                "name": str(product.Name or product.is_a())[:120],
                "ifc_type": str(product.is_a())[:64],
                "vertices": vertices,
                "triangles": triangles,
                "vertex_count": vertex_count,
                "triangle_count": face_count,
            })
            total_vertices += vertex_count
            total_triangles += face_count
        except Exception:
            # A failed shape remains visible as an explicit diagnostics count;
            # never manufacture geometry for an unreadable representation.
            failures += 1

    if not elements:
        raise ValueError("IFC mesh geometry could not be generated")
    incomplete = len(elements) + failures < len(products) or failures > 0
    result = {
        "type": "ifc_true_mesh",
        "schema": schema,
        "geometry_source": "actual_ifc_product_tessellation",
        "elements": elements,
        "rendered_element_count": len(elements),
        "represented_product_count": len(products),
        "failed_representation_count": failures,
        "partial_model": incomplete,
        "bounds": {"min": mins, "max": maxs},
        "triangle_count": total_triangles,
        "vertex_count": total_vertices,
        "clash_detection_performed": False,
        "geometry_engine": "IfcOpenShell",
        "limitations": (
            "Only tessellated visual geometry from uploaded IFC shapes; "
            "not full model federation, BREP validation, clash detection, "
            "measured quantities or construction certification."
        ),
    }
    if len(json.dumps(result, separators=(",", ":")).encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError("IFC mesh JSON exceeds visualization limit")
    return result


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        try:
            import resource
            cap = 1536 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
        except (ImportError, OSError, ValueError):
            pass
        result = extract_ifc_mesh(str(Path(sys.argv[1])))
        sys.stdout.write(json.dumps(result, separators=(",", ":")))
        return 0
    except Exception:
        # No source IFC contents or original exceptions in user-facing errors.
        return 2


if __name__ == "__main__":
    sys.exit(main())
