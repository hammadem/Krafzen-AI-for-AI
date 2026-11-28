"""Bounded deterministic queries against an original IFC STEP model.

Occurrence-level declared quantities/properties only. No estimated geometry,
type-inherited defaults, code certification, or remote AI provider calls.
"""
import json
import math
import sys

MAX_ROWS = 100
MAX_SCAN = 100000
CLASSES = {"IfcElement", "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcSpace", "IfcColumn", "IfcBeam", "IfcStair", "IfcRoof", "IfcDistributionElement"}
QUANTITY_VALUES = {
    "IfcQuantityLength": "LengthValue", "IfcQuantityArea": "AreaValue",
    "IfcQuantityVolume": "VolumeValue", "IfcQuantityCount": "CountValue",
    "IfcQuantityWeight": "WeightValue", "IfcQuantityTime": "TimeValue",
}

def brief(e):
    return {"guid": str(getattr(e,"GlobalId","") or ""), "step_id": e.id(),
            "ifc_type": str(e.is_a()), "name": str(getattr(e,"Name","") or "")[:160]}

def definitions(e, kind):
    seen = set()
    for relation in getattr(e,"IsDefinedBy",()) or ():
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        definition = getattr(relation,"RelatingPropertyDefinition",None)
        if definition and hasattr(definition,"is_a") and definition.is_a(kind) and definition.id() not in seen:
            seen.add(definition.id())
            yield definition

def same(a,b):
    return str(a or "").strip().casefold() == str(b or "").strip().casefold()

def declared_storeys(e):
    """Resolve explicit containment and aggregation, not geometric attribution."""
    pending = [e]
    visited = set()
    floors = set()
    while pending:
        obj = pending.pop()
        if obj is None or obj.id() in visited:
            continue
        visited.add(obj.id())
        if len(visited) > 64:
            raise ValueError("Spatial relationship exceeds traversal budget")
        if obj.is_a("IfcBuildingStorey"):
            floors.add(obj.id())
            continue
        for relation in getattr(obj, "ContainedInStructure", ()) or ():
            pending.append(getattr(relation, "RelatingStructure", None))
        for relation in getattr(obj, "Decomposes", ()) or ():
            if relation.is_a("IfcRelAggregates"):
                pending.append(getattr(relation, "RelatingObject", None))
    return floors


def primitive(value):
    value = getattr(value, "wrappedValue", value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (bool,int)) or value is None:
        return value
    return str(value)[:250]

def quantity_unit(q):
    unit = getattr(q,"Unit",None)
    if not unit:
        return "project_declared"
    return f"{unit.is_a()}#{unit.id()}"

def query_file(path, req):
    import ifcopenshell
    model = ifcopenshell.open(path)
    mode = req["mode"]
    entity_class = req.get("entity_class","IfcElement")
    if entity_class not in CLASSES or mode not in {"count","elements","properties","missing_property","quantity"}:
        raise ValueError("Unsupported query")
    result = {"method":"ifc_source_query_v1","schema":str(model.schema),"mode":mode,
              "entity_class":entity_class,"limits":"Explicit occurrence-level IFC declarations only; floor filter follows declared containment and aggregation; conflicting storeys are excluded and counted. No type inheritance, physical measurements or compliance conclusions."}
    storeys = model.by_type("IfcBuildingStorey")
    result["storeys"] = [brief(e) for e in storeys[:MAX_ROWS]]
    result["storeys_truncated"] = len(storeys)>MAX_ROWS
    if mode == "properties":
        guid = req.get("element_guid")
        products = model.by_type("IfcProduct")
        if len(products) > MAX_SCAN:
            raise ValueError("Product class exceeds query budget")
        matches = [e for e in products if str(getattr(e,"GlobalId","")) == guid]
        if len(matches) != 1:
            return {**result,"status":"not_found_or_ambiguous","element":None}
        e = matches[0]
        rows = []
        truncated = False
        for pset in definitions(e,"IfcPropertySet"):
            for prop in pset.HasProperties or ():
                if not prop.is_a("IfcPropertySingleValue"):
                    continue
                if len(rows) >= MAX_ROWS:
                    truncated=True
                    break
                rows.append({"set":str(pset.Name or "")[:120],"name":str(prop.Name or "")[:120],"value":primitive(prop.NominalValue),"step_id":prop.id()})
            if truncated: break
        return {**result,"status":"answered","element":brief(e),"properties":rows,"truncated":truncated}
    elements = model.by_type(entity_class)
    if len(elements)>MAX_SCAN:
        raise ValueError("Model class exceeds query budget")
    storey_guid = req.get("storey_guid")
    if storey_guid:
        matches = [e for e in storeys if str(e.GlobalId) == storey_guid]
        if len(matches) != 1:
            return {**result,"status":"not_found_or_ambiguous","match_count":None}
        target = matches[0].id()
        selected = []
        ambiguous = 0
        for e in elements:
            floors = declared_storeys(e)
            if target in floors:
                if len(floors) == 1:
                    selected.append(e)
                else:
                    ambiguous += 1
        elements = selected
        result["ambiguous_storey_count"] = ambiguous
        result["storey_relationship_method"] = "explicit_containment_and_aggregation"
    result["match_count"] = len(elements)
    result["status"] = "answered"
    if mode in {"count","elements"}:
        if mode=="elements":
            result["elements"]=[brief(e) for e in elements[:MAX_ROWS]]
            result["truncated"]=len(elements)>MAX_ROWS
        return result
    set_name, property_name = req.get("set_name"),req.get("property_name")
    if not str(set_name or "").strip() or not str(property_name or "").strip():
        raise ValueError("Exact set and property name required")
    if mode == "missing_property":
        missing = []
        missing_count=0
        for e in elements:
            present=any(same(pset.Name,set_name) and any(
                same(prop.Name,property_name) and prop.is_a("IfcPropertySingleValue") and
                getattr(prop,"NominalValue",None) is not None and primitive(prop.NominalValue) not in (None,"")
                for prop in pset.HasProperties or ()) for pset in definitions(e,"IfcPropertySet"))
            if not present:
                missing_count+=1
                if len(missing)<MAX_ROWS: missing.append(brief(e))
        return {**result,"missing_count":missing_count,"elements":missing,"truncated":missing_count>MAX_ROWS,
                "status":"answered","property_name":property_name,"set_name":set_name}
    totals={}
    missing=0
    ambiguous=0
    for e in elements:
        seen={}
        for qset in definitions(e,"IfcElementQuantity"):
            if not same(qset.Name,set_name): continue
            for q in qset.Quantities or ():
                if same(q.Name,property_name): seen[q.id()]=q
        if len(seen)>1:
            ambiguous+=1
            continue
        if not seen:
            missing+=1
            continue
        q=next(iter(seen.values()))
        kind=str(q.is_a())
        attr=QUANTITY_VALUES.get(kind)
        try: value=float(getattr(q,attr)) if attr else None
        except (TypeError,ValueError,AttributeError): value=None
        if value is None or not math.isfinite(value) or not 0 <= value <= 1e15:
            missing+=1
            continue
        unit=quantity_unit(q)
        item=totals.setdefault((kind,unit),{"type":kind,"unit":unit,"sum_raw":0.0,"item_count":0})
        item["sum_raw"]+=value
        item["item_count"]+=1
        if len(totals)>MAX_ROWS:
            raise ValueError("Quantity unit grouping exceeds query budget")
    return {**result,"quantity_name":property_name,"set_name":set_name,"totals":list(totals.values()),
            "missing_count":missing,"ambiguous_count":ambiguous,"quantities_are_declared_not_measured":True}

def main():
    if len(sys.argv)!=2: return 2
    try:
        try:
            import resource
            cap=1024*1024*1024
            resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
        except (ImportError,OSError,ValueError): pass
        raw=sys.stdin.buffer.read(8193)
        if len(raw)>8192: return 2
        result=query_file(sys.argv[1],json.loads(raw))
        sys.stdout.write(json.dumps(result,allow_nan=False,separators=(",",":")))
        return 0
    except Exception:
        return 2

if __name__=="__main__":
    sys.exit(main())
