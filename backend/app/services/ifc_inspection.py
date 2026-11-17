"""Parse IFC model content with IfcOpenShell, without inventing BIM geometry.

Executed in a bounded subprocess by import_service. The returned data
describes entities present in the STEP file; it is not a clash analysis,
geometry certification, or engineering compliance validation.
"""

import json
import sys
from collections import Counter
from pathlib import Path


def inspect_ifc_file(path: str) -> dict:
    import ifcopenshell

    model = ifcopenshell.open(path)
    schema = str(model.schema).upper()
    if schema not in {"IFC2X3", "IFC4"} and not schema.startswith("IFC4X3"):
        raise ValueError("Unsupported IFC schema")

    projects = model.by_type("IfcProject")
    if len(projects) != 1:
        raise ValueError("IFC model must have exactly one IfcProject")

    project = projects[0]
    products = model.by_type("IfcProduct")
    if not products:
        raise ValueError("IFC model has no identifiable spatial or model products")

    counts = Counter(str(entity.is_a()) for entity in products)
    project_id = str(project.GlobalId or "")
    if not project_id or len(project_id) != 22:
        raise ValueError("IFC project identifier is missing or invalid")

    # IFC model entities are not necessarily valid 3-D bodies. Distinguish
    # declared representations from geometrically verified shape results.
    represented = sum(1 for entity in products if getattr(entity, "Representation", None))
    return {
        "type": "ifc",
        "schema": schema,
        "project_name": str(project.Name or "")[:250],
        "project_global_id": project_id,
        "product_count": len(products),
        "element_count": len(model.by_type("IfcElement")),
        "spatial_count": (
            len(model.by_type("IfcSpatialStructureElement"))
            if schema in {"IFC2X3", "IFC4"}
            else len(model.by_type("IfcSpatialElement"))
        ),
        "represented_product_count": represented,
        "entity_counts": dict(sorted(counts.items())[:80]),
        "geometry_validated": False,
        "clash_detection_performed": False,
    }


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        # IFC parsing runs in another process, not in the API/worker process.
        # Linux-only resource limit protects the primary service from runaway
        # STEP parsing; outside Linux the caller still enforces a timeout.
        try:
            import resource
            max_virtual_memory = 1024 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_virtual_memory, max_virtual_memory))
        except (ImportError, OSError, ValueError):
            pass
        summary = inspect_ifc_file(str(Path(sys.argv[1])))
    except Exception:
        # Never echo untrusted IFC content or filesystem paths to HTTP clients.
        return 2
    sys.stdout.write(json.dumps(summary, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
