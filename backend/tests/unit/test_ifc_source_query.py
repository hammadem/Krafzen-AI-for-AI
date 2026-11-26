import ifcopenshell
from app.services.ifc_source_query import query_file

def test_ifc_count_floor_properties_and_quantity(tmp_path):
    model=ifcopenshell.file(schema="IFC4")
    def guid(): return ifcopenshell.guid.new()
    model.create_entity("IfcProject",GlobalId=guid(),Name="QA")
    floor=model.create_entity("IfcBuildingStorey",GlobalId=guid(),Name="Level 1")
    a=model.create_entity("IfcWall",GlobalId=guid(),Name="Wall A")
    b=model.create_entity("IfcWall",GlobalId=guid(),Name="Wall B")
    model.create_entity("IfcRelContainedInSpatialStructure",GlobalId=guid(),RelatedElements=[a],RelatingStructure=floor)
    prop=model.create_entity("IfcPropertySingleValue",Name="FireRating",NominalValue=model.create_entity("IfcLabel","QA declared value"))
    pset=model.create_entity("IfcPropertySet",GlobalId=guid(),Name="Pset_WallCommon",HasProperties=[prop])
    model.create_entity("IfcRelDefinesByProperties",GlobalId=guid(),RelatedObjects=[a],RelatingPropertyDefinition=pset)
    qty=model.create_entity("IfcQuantityLength",Name="Length",LengthValue=2.5)
    qset=model.create_entity("IfcElementQuantity",GlobalId=guid(),Name="Qto_WallBaseQuantities",Quantities=[qty])
    model.create_entity("IfcRelDefinesByProperties",GlobalId=guid(),RelatedObjects=[a,b],RelatingPropertyDefinition=qset)
    path=tmp_path/"query.ifc";model.write(str(path))
    def run(**req): return query_file(str(path),{"entity_class":"IfcWall",**req})
    assert run(mode="count")["match_count"]==2
    assert run(mode="elements",storey_guid=floor.GlobalId)["elements"][0]["guid"]==a.GlobalId
    assert run(mode="properties",element_guid=a.GlobalId)["properties"][0]["value"]=="QA declared value"
    assert run(mode="properties",element_guid=guid())["status"]=="not_found_or_ambiguous"
    missing=run(mode="missing_property",set_name="Pset_WallCommon",property_name="FireRating")
    assert missing["missing_count"]==1 and missing["elements"][0]["guid"]==b.GlobalId
    quantities=run(mode="quantity",set_name="Qto_WallBaseQuantities",property_name="Length")
    assert quantities["totals"]==[{"type":"IfcQuantityLength","unit":"project_declared","sum_raw":5.0,"item_count":2}]
    assert quantities["quantities_are_declared_not_measured"] is True


def test_ifc_floor_query_includes_aggregated_spaces_and_contained_elements(tmp_path):
    model = ifcopenshell.file(schema="IFC4")
    def guid(): return ifcopenshell.guid.new()
    floor = model.create_entity("IfcBuildingStorey", GlobalId=guid(), Name="Level 1")
    space = model.create_entity("IfcSpace", GlobalId=guid(), Name="Room 101")
    wall = model.create_entity("IfcWall", GlobalId=guid())
    model.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=floor, RelatedObjects=[space])
    model.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=space, RelatedElements=[wall])
    path = tmp_path / "hierarchy.ifc"
    model.write(str(path))
    for kind, obj in (("IfcSpace", space), ("IfcWall", wall)):
        result = query_file(str(path), {"mode": "elements", "entity_class": kind, "storey_guid": floor.GlobalId})
        assert result["match_count"] == 1
        assert result["elements"][0]["guid"] == obj.GlobalId
        assert result["ambiguous_storey_count"] == 0


def test_ifc_floor_query_excludes_conflicting_declared_storeys(tmp_path):
    model = ifcopenshell.file(schema="IFC4")
    def guid(): return ifcopenshell.guid.new()
    first = model.create_entity("IfcBuildingStorey", GlobalId=guid())
    second = model.create_entity("IfcBuildingStorey", GlobalId=guid())
    wall = model.create_entity("IfcWall", GlobalId=guid())
    model.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=first, RelatedElements=[wall])
    model.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=second, RelatedObjects=[wall])
    path = tmp_path / "conflict.ifc"
    model.write(str(path))
    result = query_file(str(path), {"mode": "count", "entity_class": "IfcWall", "storey_guid": first.GlobalId})
    assert result["match_count"] == 0
    assert result["ambiguous_storey_count"] == 1
