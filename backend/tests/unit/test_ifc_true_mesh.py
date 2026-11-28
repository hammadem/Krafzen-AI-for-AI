"""Real represented IFC solid tessellation and storage-scoped visualization."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import ifcopenshell
import pytest
from fastapi import HTTPException

from app.routes import bim_geometry_routes as routes
from app.services.ifc_mesh_extraction import extract_ifc_mesh

PROJECT = "00000000-0000-0000-0000-000000000002"
JOB = "00000000-0000-0000-0000-000000000003"
FILE = "00000000-0000-0000-0000-000000000004"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


def create_real_solid(path: Path):
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
        Position=axis2d, XDim=2.0, YDim=0.2,
    )
    z = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    solid = model.create_entity(
        "IfcExtrudedAreaSolid", SweptArea=profile,
        Position=axis3d, ExtrudedDirection=z, Depth=3.0,
    )
    shape = model.create_entity(
        "IfcShapeRepresentation", ContextOfItems=context,
        RepresentationIdentifier="Body", RepresentationType="SweptSolid",
        Items=[solid],
    )
    wall = model.create_entity(
        "IfcWall", GlobalId=ifcopenshell.guid.new(), Name="Measured 2m wall",
        ObjectPlacement=model.create_entity(
            "IfcLocalPlacement", RelativePlacement=axis3d
        ),
        Representation=model.create_entity(
            "IfcProductDefinitionShape", Representations=[shape]
        ),
    )
    model.write(str(path))
    return path.read_bytes(), str(wall.GlobalId)


def test_3d_mesh_has_real_ifc_representation_triangles(tmp_path):
    path = tmp_path / "real-wall.ifc"
    _, guid = create_real_solid(path)
    mesh = extract_ifc_mesh(str(path))
    assert mesh["type"] == "ifc_true_mesh"
    assert mesh["geometry_source"] == "actual_ifc_product_tessellation"
    assert mesh["rendered_element_count"] == 1
    assert mesh["triangle_count"] >= 12
    assert mesh["vertex_count"] >= 8
    assert mesh["elements"][0]["guid"] == guid
    assert mesh["elements"][0]["ifc_type"] == "IfcWall"
    assert len(mesh["elements"][0]["vertices"]) % 3 == 0
    assert len(mesh["elements"][0]["triangles"]) % 3 == 0
    assert mesh["bounds"]["max"][2] == pytest.approx(3, abs=1e-4)
    assert mesh["clash_detection_performed"] is False


def test_unrepresented_ifc_product_never_yields_fake_3d(tmp_path):
    model = ifcopenshell.file(schema="IFC4")
    model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new())
    model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new())
    path = tmp_path / "no-geometry.ifc"
    model.write(str(path))
    with pytest.raises(ValueError, match="No products"):
        extract_ifc_mesh(str(path))


@pytest.mark.asyncio
async def test_private_model_geometry_route_reads_correct_owned_ifc(tmp_path):
    path = tmp_path / "real-wall.ifc"
    raw, guid = create_real_solid(path)
    stored_path = f"{USER['user_id']}/{PROJECT}/imports/{JOB}/import_wall.ifc"
    source = {
        "id": FILE, "project_id": PROJECT, "job_id": JOB,
        "path": stored_path, "bucket": "dxf-files", "file_type": "ifc",
        "size_bytes": len(raw), "import_metadata": {"type": "ifc"},
    }
    client = MagicMock()
    client.storage.from_.return_value.download.return_value = raw

    async def inline(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch.object(routes, "get_file", AsyncMock(return_value=source)),
        patch.object(routes, "get_project",
                     AsyncMock(return_value={"id": PROJECT, "workspace_id": None})),
        patch.object(routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(routes, "run_in_threadpool", inline),
    ):
        response = await routes.get_model_mesh(UUID(FILE), user=USER)
    assert response["file_id"] == FILE
    assert response["mesh"]["elements"][0]["guid"] == guid
    assert response["mesh"]["triangle_count"] >= 12
    client.storage.from_.return_value.download.assert_called_once_with(stored_path)


@pytest.mark.asyncio
@pytest.mark.parametrize("problem", [
    {"path": "../../other-user/model.ifc"},
    {"path": f"{USER['user_id']}/{PROJECT}/imports/{JOB}/../other.ifc"},
    {"bucket": "different-tenant"},
    {"size_bytes": -1},
    {"file_type": "dxf"},
    {"import_metadata": {}},
])
async def test_untrusted_or_unverified_ifc_fails_before_private_download(problem):
    source = {
        "id": FILE, "project_id": PROJECT, "job_id": JOB,
        "path": f"{USER['user_id']}/{PROJECT}/imports/{JOB}/model.ifc",
        "bucket": "dxf-files", "file_type": "ifc",
        "size_bytes": 1000, "import_metadata": {"type": "ifc"},
        **problem,
    }
    client = MagicMock()
    with (
        patch.object(routes, "get_file", AsyncMock(return_value=source)),
        patch.object(routes, "get_project",
                     AsyncMock(return_value={"id": PROJECT, "workspace_id": None})),
        patch.object(routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
    ):
        with pytest.raises(HTTPException) as error:
            await routes.get_model_mesh(UUID(FILE), user=USER)
    assert error.value.status_code in (409, 413, 415)
    client.storage.from_.return_value.download.assert_not_called()


@pytest.mark.asyncio
async def test_sovereign_model_never_uses_global_storage():
    with (
        patch.object(routes, "get_file", AsyncMock(return_value={
            "id": FILE, "project_id": PROJECT, "file_type": "ifc"
        })),
        patch.object(routes, "get_project", AsyncMock(return_value={
            "id": PROJECT, "workspace_id": "sovereign-organization"
        })),
        patch.object(routes.storage_service, "resolve_target_bucket_and_client") as resolver,
    ):
        with pytest.raises(HTTPException) as error:
            await routes.get_model_mesh(UUID(FILE), user=USER)
    assert error.value.status_code == 503
    resolver.assert_not_called()
