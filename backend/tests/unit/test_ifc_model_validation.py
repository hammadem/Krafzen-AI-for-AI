from pathlib import Path
import ifcopenshell

from app.services.ifc_model_validation import analyze_ifc
from tests.unit.test_ifc_native_coordination import create_real_solid


def test_validation_uses_actual_model_properties_and_geometry(tmp_path: Path):
    path=tmp_path/"solid.ifc"
    _, guid=create_real_solid(path)
    model=ifcopenshell.open(str(path))
    wall=model.by_type("IfcWall")[0]
    prop=model.create_entity("IfcPropertySingleValue",Name="FireRating",NominalValue=model.create_entity("IfcLabel","QA fixture"))
    pset=model.create_entity("IfcPropertySet",GlobalId=ifcopenshell.guid.new(),Name="Pset_WallCommon",HasProperties=[prop])
    model.create_entity("IfcRelDefinesByProperties",GlobalId=ifcopenshell.guid.new(),RelatedObjects=[wall],RelatingPropertyDefinition=pset)
    model.write(str(path))
    result=analyze_ifc(str(path))
    assert result["schema_attribute_validation_performed"] is True
    assert result["geometry_checked_count"] == 1
    assert result["geometry_failed_count"] == 0
    assert result["physical_class_counts"]["IfcWall"] == 1
    found=next(x for x in result["element_inventory"] if x["guid"]==guid)
    assert found["declared_properties"]["Pset_WallCommon"]["FireRating"] == "QA fixture"
    assert result["complete_model_validity_determined"] is False


def test_duplicate_global_ids_and_missing_containment_are_visible(tmp_path: Path):
    path=tmp_path/"duplicate.ifc"
    _,guid=create_real_solid(path)
    model=ifcopenshell.open(str(path))
    model.create_entity("IfcWall",GlobalId=guid,Name="duplicate")
    model.write(str(path))
    result=analyze_ifc(str(path))
    assert result["finding_counts"]["duplicate_global_id"] >= 2
    assert result["finding_counts"]["spatial_container_not_observed"] >= 1
    assert result["finding_counts"]["representation_not_observed"] >= 1
    assert result["requires_professional_review"] is True
