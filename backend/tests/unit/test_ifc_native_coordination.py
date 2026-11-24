"""Real native IFC fixtures, not fabricated bounding-box clashes."""
from pathlib import Path

import ifcopenshell
import pytest

from app.services.ifc_native_coordination import coordinate_ifc_models

def create_real_solid(path: Path, offset=(0.0, 0.0, 0.0), dims=(2.0, 0.2, 3.0)):
    """Write a valid extruded IFC wall, not a fake polygon list."""
    model = ifcopenshell.file(schema="IFC4")
    origin = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    axis3d = model.create_entity("IfcAxis2Placement3D", Location=origin)
    origin2d = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0))
    axis2d = model.create_entity("IfcAxis2Placement2D", Location=origin2d)
    context = model.create_entity(
        "IfcGeometricRepresentationContext",
        ContextIdentifier="Model", ContextType="Model",
        CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=axis3d,
    )
    metre = model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    units = model.create_entity("IfcUnitAssignment", Units=[metre])
    model.create_entity(
        "IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Actual warehouse",
        RepresentationContexts=[context], UnitsInContext=units,
    )
    profile = model.create_entity(
        "IfcRectangleProfileDef", ProfileType="AREA", ProfileName="2m wall",
        Position=axis2d, XDim=dims[0], YDim=dims[1],
    )
    z = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    solid = model.create_entity(
        "IfcExtrudedAreaSolid", SweptArea=profile,
        Position=axis3d, ExtrudedDirection=z, Depth=dims[2],
    )
    shape = model.create_entity(
        "IfcShapeRepresentation", ContextOfItems=context,
        RepresentationIdentifier="Body", RepresentationType="SweptSolid",
        Items=[solid],
    )
    placement = model.create_entity("IfcAxis2Placement3D", Location=model.create_entity("IfcCartesianPoint", Coordinates=offset))
    wall = model.create_entity(
        "IfcWall", GlobalId=ifcopenshell.guid.new(), Name="Measured 2m wall",
        ObjectPlacement=model.create_entity(
            "IfcLocalPlacement", RelativePlacement=placement
        ),
        Representation=model.create_entity(
            "IfcProductDefinitionShape", Representations=[shape]
        ),
    )
    model.write(str(path))
    return path.read_bytes(), str(wall.GlobalId)



def test_native_contained_solid_intersection(tmp_path):
    a, b = tmp_path / "a.ifc", tmp_path / "b.ifc"
    _, guid_a = create_real_solid(a)
    _, guid_b = create_real_solid(b, offset=(0.2, 0.02, 0.5), dims=(0.8, 0.08, 1.0))
    report = coordinate_ifc_models(str(a), str(b), 0.05)
    assert report["method"] == "ifcopenshell_native_intersection_clearance_v1"
    assert report["analysis_partial"] is False
    assert report["hard_clashes_confirmed"] >= 1
    hit = next(x for x in report["candidates"] if x["classification"] == "hard_clash")
    assert {hit["source"]["guid"], hit["target"]["guid"]} == {guid_a, guid_b}
    assert hit["distance_m"] > 0.002
    assert len(hit["location_a_m"]) == len(hit["location_b_m"]) == 3


def test_native_clearance_uses_actual_surface_distance(tmp_path):
    a, b = tmp_path / "a.ifc", tmp_path / "b.ifc"
    create_real_solid(a)
    create_real_solid(b, offset=(0.0, 0.23, 0.0))
    report = coordinate_ifc_models(str(a), str(b), 0.05)
    assert report["hard_clashes_confirmed"] == 0
    assert report["clearance_conflict_count"] == 1
    hit = next(x for x in report["candidates"] if x["classification"] == "clearance_conflict")
    assert hit["distance_m"] == pytest.approx(0.03, abs=0.002)
    assert report["requires_professional_review"] is True


def test_native_separate_models_have_no_findings_but_no_certification(tmp_path):
    a, b = tmp_path / "a.ifc", tmp_path / "b.ifc"
    create_real_solid(a)
    create_real_solid(b, offset=(20.0, 20.0, 0.0))
    report = coordinate_ifc_models(str(a), str(b), 0.05)
    assert report["candidate_count"] == 0
    assert report["requires_professional_review"] is True
    assert all(x["indexed_element_count"] == 1 for x in report["source_models"])


@pytest.mark.parametrize("clearance", [0, -1, 2, float("nan")])
def test_invalid_clearance_rejected_before_open(clearance):
    with pytest.raises(ValueError, match="Clearance"):
        coordinate_ifc_models("not-present.ifc", "not-present.ifc", clearance)
