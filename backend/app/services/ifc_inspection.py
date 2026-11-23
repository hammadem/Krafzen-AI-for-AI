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

    # Model structure comes from actual IFC spatial containment assignments.
    # No manufactured floor geometry or assumptions about IFC units.
    storeys = model.by_type("IfcBuildingStorey")
    levels = []
    for storey in storeys[:100]:
        assignments = getattr(storey, "ContainsElements", ()) or ()
        assigned = sum(len(rel.RelatedElements) for rel in assignments)
        levels.append({
            "global_id": str(storey.GlobalId),
            "name": str(storey.Name or "")[:160],
            "elevation": getattr(storey, "Elevation", None),
            "contained_element_count": assigned,
        })

    # Extract only project-level declared model length units. Report raw IFC
    # values without translating or inventing dimensional accuracy.
    length_unit = None
    units = getattr(project, "UnitsInContext", None)
    for unit in (getattr(units, "Units", ()) or ()):
        if unit.is_a("IfcSIUnit") and str(unit.UnitType) == "LENGTHUNIT":
            length_unit = {
                "name": str(unit.Name),
                "prefix": str(unit.Prefix) if unit.Prefix else None,
            }
            break

    # Read *declared* IFC quantities and property sets actually assigned to
    # model products. Never estimate dimensions from counts or claim a geometric
    # takeoff without evaluating representations.
    quantity_totals: dict[str, dict] = {}
    property_set_counts: Counter = Counter()
    quantity_relations = 0
    for rel in model.by_type("IfcRelDefinesByProperties")[:50000]:
        definition = getattr(rel, "RelatingPropertyDefinition", None)
        if not definition:
            continue
        assigned = sum(
            1 for obj in (getattr(rel, "RelatedObjects", ()) or ())
            if obj.is_a("IfcProduct")
        )
        if not assigned:
            continue
        if definition.is_a("IfcPropertySet"):
            property_set_counts[str(definition.Name or "Unnamed")[:120]] += assigned
            continue
        if not definition.is_a("IfcElementQuantity"):
            continue
        quantity_relations += 1
        set_name = str(definition.Name or "Unnamed")[:100]
        for qty in (getattr(definition, "Quantities", ()) or ()):
            kind = str(qty.is_a())
            value_attr = {
                "IfcQuantityLength": "LengthValue",
                "IfcQuantityArea": "AreaValue",
                "IfcQuantityVolume": "VolumeValue",
                "IfcQuantityCount": "CountValue",
                "IfcQuantityWeight": "WeightValue",
                "IfcQuantityTime": "TimeValue",
            }.get(kind)
            if not value_attr:
                continue
            try:
                value = float(getattr(qty, value_attr))
            except (TypeError, ValueError, AttributeError):
                continue
            if not (-1e15 <= value <= 1e15):
                continue
            name = str(qty.Name or kind)[:100]
            unit = getattr(qty, "Unit", None)
            # Unit overrides are not silently combined with project defaults.
            unit_key = f"{unit.is_a()}:{unit.id()}" if unit else "project_declared"
            key = f"{set_name}/{name}/{kind}/{unit_key}"
            if key not in quantity_totals and len(quantity_totals) >= 300:
                continue
            item = quantity_totals.setdefault(key, {
                "set": set_name, "name": name, "type": kind,
                "unit": unit_key,
                "sum_raw": 0.0, "item_count": 0,
            })
            item["sum_raw"] += value * assigned
            item["item_count"] += assigned

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
        "storeys": levels,
        "storey_count": len(storeys),
        "length_unit": length_unit,
        "represented_product_count": represented,
        "declared_quantities": list(quantity_totals.values()),
        "quantity_relation_count": quantity_relations,
        "property_set_assignment_counts": dict(sorted(property_set_counts.items())[:200]),
        "quantities_are_declared_not_measured": True,
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
