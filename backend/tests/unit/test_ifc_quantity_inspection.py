"""Real IFC quantity and property-set extraction; never fake geometry results."""
from pathlib import Path

import ifcopenshell

from app.services.ifc_inspection import inspect_ifc_file


def test_ifc_takeoff_uses_declared_quantities_and_real_assignments(tmp_path: Path):
    model = ifcopenshell.file(schema="IFC4")
    project = model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Quantities")
    metre = model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    project.UnitsInContext = model.create_entity("IfcUnitAssignment", Units=[metre])
    wall = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(), Name="W-01")
    length = model.create_entity("IfcQuantityLength", Name="NetLength", LengthValue=5.25)
    qset = model.create_entity(
        "IfcElementQuantity", GlobalId=ifcopenshell.guid.new(),
        Name="Qto_WallBaseQuantities", Quantities=[length],
    )
    model.create_entity(
        "IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[wall], RelatingPropertyDefinition=qset,
    )
    prop = model.create_entity(
        "IfcPropertySingleValue", Name="AcousticRating",
        NominalValue=model.create_entity("IfcLabel", "Rw50")
    )
    pset = model.create_entity(
        "IfcPropertySet", GlobalId=ifcopenshell.guid.new(),
        Name="Pset_WallCommon", HasProperties=[prop],
    )
    model.create_entity(
        "IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[wall], RelatingPropertyDefinition=pset,
    )
    path = tmp_path / "quantities.ifc"
    model.write(str(path))
    report = inspect_ifc_file(str(path))
    assert report["schema"] == "IFC4"
    assert report["element_count"] == 1
    assert report["entity_counts"]["IfcWall"] == 1
    assert report["quantity_relation_count"] == 1
    assert len(report["declared_quantities"]) == 1
    result = report["declared_quantities"][0]
    assert result["set"] == "Qto_WallBaseQuantities"
    assert result["name"] == "NetLength"
    assert result["sum_raw"] == 5.25
    assert result["item_count"] == 1
    assert result["unit"] == "project_declared"
    assert report["property_set_assignment_counts"]["Pset_WallCommon"] == 1
    assert report["quantities_are_declared_not_measured"] is True
    assert report["geometry_validated"] is False
    assert report["clash_detection_performed"] is False


def test_unassigned_quantity_sets_are_not_falsely_counted(tmp_path: Path):
    model = ifcopenshell.file(schema="IFC4")
    model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Shed")
    model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new())
    quantity = model.create_entity("IfcQuantityArea", Name="GrossArea", AreaValue=99.0)
    model.create_entity(
        "IfcElementQuantity", GlobalId=ifcopenshell.guid.new(),
        Name="Orphaned", Quantities=[quantity]
    )
    path = tmp_path / "orphan.ifc"
    model.write(str(path))
    summary = inspect_ifc_file(str(path))
    assert summary["declared_quantities"] == []
    assert summary["quantity_relation_count"] == 0
