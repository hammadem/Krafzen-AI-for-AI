"""Source-backed IFC schema, identity, topology and representation diagnostics.

No generative inference: each observation comes from the parsed IFC population
or an actual native tessellation. Not structural, regulatory or IDS approval.
"""
import json
import math
import sys
from collections import Counter

MAX_FINDINGS = 250
MAX_ELEMENTS = 200
MAX_ENTITY_COUNT = 100000


def analyze_ifc(path):
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.validate
    from ifcopenshell.util.element import get_container, get_psets

    model = ifcopenshell.open(path)
    schema = str(model.schema)
    if schema not in {"IFC2X3", "IFC4"} and not schema.startswith("IFC4X3"):
        raise ValueError("Unsupported IFC schema")
    if sum(1 for _ in model) > MAX_ENTITY_COUNT:
        raise ValueError("Model exceeds validation budget")
    findings, counts = [], Counter()

    def reference(entity):
        if not hasattr(entity, "id"):
            return {"step_id": None, "guid": None, "ifc_type": None}
        return {"step_id": entity.id(), "guid": str(getattr(entity, "GlobalId", "") or "")[:32] or None,
                "ifc_type": str(entity.is_a())}

    def report(category, severity, entity=None, message=None, **details):
        counts[category] += 1
        if len(findings) < MAX_FINDINGS:
            findings.append({"category": category, "severity": severity,
                             **reference(entity), "message": str(message or "")[:600], **details})

    # The IfcOpenShell validator checks entity attribute types, required
    # attributes, inverse cardinality, and captured parser diagnostics.
    # EXPRESS WHERE rules and independent SPF syntax verification are separate.
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(path), logger, express_rules=False)
    for row in logger.statements:
        report("schema_or_parser_diagnostic", "review", row.get("instance"),
               row.get("message"), attribute=str(row.get("attribute") or "")[:160],
               validator_level=str(row.get("level") or "")[:40])

    roots = model.by_type("IfcRoot")
    ids = Counter(str(e.GlobalId or "") for e in roots)
    for element in roots:
        guid = str(element.GlobalId or "")
        if not guid or ifcopenshell.validate.validate_guid(guid):
            report("invalid_global_id", "high", element, "GlobalId is missing or invalid")
        elif ids[guid] > 1:
            report("duplicate_global_id", "high", element,
                   "Multiple IFC roots declare the same GlobalId", occurrence_count=ids[guid])

    elements = [x for x in model.by_type("IfcElement")
                if not x.is_a("IfcFeatureElementSubtraction")]
    ports = model.by_type("IfcDistributionPort")
    connected_port_ids = set()
    relationships = model.by_type("IfcRelConnectsPorts")
    for rel in relationships:
        for endpoint in (getattr(rel, "RelatingPort", None), getattr(rel, "RelatedPort", None)):
            if endpoint:
                connected_port_ids.add(endpoint.id())
    for port in ports:
        if port.id() not in connected_port_ids:
            report("port_without_declared_connection", "review", port,
                   "No IfcRelConnectsPorts relationship found; terminals and intentionally open ports require reviewer interpretation")

    geom_settings = ifcopenshell.geom.settings()
    geom_settings.set(geom_settings.USE_WORLD_COORDS, True)
    represented = [e for e in elements if getattr(e, "Representation", None)]
    geometry_checked = 0
    geometry_failed = 0
    for element in represented[:MAX_ELEMENTS]:
        geometry_checked += 1
        try:
            shape = ifcopenshell.geom.create_shape(geom_settings, element)
            verts, faces = shape.geometry.verts, shape.geometry.faces
            if (len(verts) < 9 or len(verts) % 3 or len(faces) < 3 or len(faces) % 3
                or not all(math.isfinite(x) and abs(x) <= 1e9 for x in verts)
                or any(i < 0 or i >= len(verts)//3 for i in faces)):
                raise ValueError("Empty or invalid tessellation")
        except Exception:
            geometry_failed += 1
            report("geometry_unprocessable", "high", element, "Represented element could not produce a valid bounded triangle mesh")
    for element in elements:
        try:
            container = get_container(element)
            if container is None:
                report("spatial_container_not_observed", "review", element,
                       "No spatial container resolved; confirm spatial decomposition and applicable exceptions")
        except Exception:
            report("spatial_lookup_failed", "review", element, "Spatial relationship lookup failed")
        if not getattr(element, "Representation", None):
            report("representation_not_observed", "review", element,
                   "No direct representation declared; type-mapped geometry or intentional omission requires review")

    # Bounded element property inspector. Values are source declarations, not
    # independently measured facts; no implicit unit conversion or estimates.
    def scalar(value):
        if isinstance(value, bool) or value is None: return value
        if isinstance(value, (int,float)):
            return value if math.isfinite(value) else None
        if isinstance(value, str): return value[:200]
        if isinstance(value, (list,tuple)): return [scalar(v) for v in value[:10]]
        return str(value)[:200]

    inventory=[]
    for element in elements[:MAX_ELEMENTS]:
        properties={}
        try:
            raw = get_psets(element, should_inherit=True)
            for key, values in sorted(raw.items())[:15]:
                if isinstance(values,dict):
                    properties[str(key)[:100]] = {
                        str(k)[:100]:scalar(v) for k,v in list(values.items())[:15] if k!="id"}
            if not properties:
                report("property_sets_not_observed", "review", element,
                       "No property sets or declared quantities found in bounded property inspection; project-specific requirements unknown")
        except Exception:
            report("property_lookup_failed", "review", element, "Property extraction failed")
        try:
            container=get_container(element)
        except Exception:
            container=None
        inventory.append({**reference(element), "name":str(element.Name or "")[:120],
                          "container":reference(container) if container else None,
                          "container_name":str(getattr(container,"Name","") or "")[:120],
                          "declared_properties":properties})
    return {
        "method":"ifcopenshell_source_validation_v1","schema":schema,
        "schema_attribute_validation_performed":True,"express_where_rules_performed":False,
        "independent_spf_syntax_validation_performed":False,
        "finding_counts":dict(sorted(counts.items())),"finding_count":sum(counts.values()),
        "findings":findings,"findings_truncated":sum(counts.values())>len(findings),
        "element_count":len(elements),"physical_class_counts":dict(sorted(Counter(e.is_a() for e in elements).items())),
        "represented_count":len(represented),"geometry_checked_count":geometry_checked,
        "geometry_failed_count":geometry_failed,
        "declared_port_count":len(ports),"declared_connected_port_count":len(connected_port_ids),
        "port_relationship_count":len(relationships),
        "element_inventory":inventory,"inventory_truncated":len(elements)>len(inventory),
        "analysis_partial":geometry_checked<len(represented) or len(elements)>len(inventory),
        "complete_model_validity_determined":False,"requires_professional_review":True,
        "limitations":"IFC attribute and inverse cardinality diagnostics, duplicate IDs, source-declared properties/ports/containment and bounded native tessellation only. Independent SPF syntax checks, EXPRESS WHERE rules, IDS requirements, geometric manifold integrity, full MEP system connectivity, quantity accuracy and physical/code compliance are not certified. Missing port relationships or property sets require project-specific review. No findings does not prove a valid model."
    }


def main():
    if len(sys.argv)!=2: return 2
    try:
        try:
            import resource
            cap=1536*1024*1024
            resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
        except (ImportError,OSError,ValueError):
            pass
        result=analyze_ifc(sys.argv[1])
        payload=json.dumps(result,allow_nan=False,separators=(",",":"))
        if len(payload.encode("utf-8"))>8*1024*1024: return 2
        print(payload)
        return 0
    except Exception:
        return 2

if __name__=="__main__":
    sys.exit(main())
