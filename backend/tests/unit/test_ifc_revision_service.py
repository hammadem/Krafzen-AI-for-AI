from pathlib import Path
import ifcopenshell
from app.services.ifc_mesh_extraction import extract_ifc_mesh
from app.services.ifc_revision_service import compare_ifc_mesh_revisions
from tests.unit.test_ifc_native_coordination import create_real_solid


def test_actual_ifc_revision_changed_geometry(tmp_path: Path):
    a, b = tmp_path / "a.ifc", tmp_path / "b.ifc"
    _, guid = create_real_solid(a)
    create_real_solid(b, offset=(1.0, 0.0, 0.0))
    model = ifcopenshell.open(str(b))
    model.by_type("IfcWall")[0].GlobalId = guid
    model.write(str(b))
    result = compare_ifc_mesh_revisions(extract_ifc_mesh(str(a)), extract_ifc_mesh(str(b)))
    assert result["revision"]["counts"] == {"tessellation_or_placement_changed": 1}
    assert result["revision"]["changes"][0]["guid"] == guid
    assert result["analysis_partial"] is False


def test_missing_from_partial_mesh_is_uncertain(tmp_path: Path):
    a, b = tmp_path / "a.ifc", tmp_path / "b.ifc"
    create_real_solid(a)
    create_real_solid(b)
    original, revised = extract_ifc_mesh(str(a)), extract_ifc_mesh(str(b))
    revised["partial_model"] = True
    result = compare_ifc_mesh_revisions(original, revised)
    assert result["revision"]["counts"]["not_observed_in_revised"] == 1
    assert "removed_from_mesh" not in result["revision"]["counts"]
