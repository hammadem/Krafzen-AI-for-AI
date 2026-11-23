"""BIM source-linked AABB screening: candidate geometry and project ACL tests."""
from math import inf
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.routes import bim_geometry_routes as routes
from app.services.ifc_spatial_screen import screen_ifc_mesh_overlap


USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
PROJECT = "00000000-0000-0000-0000-000000000002"
FIRST = "00000000-0000-0000-0000-000000000003"
SECOND = "00000000-0000-0000-0000-000000000004"


def _box(origin, extent, guid):
    x, y, z = origin
    dx, dy, dz = extent
    vertices = [
        x, y, z, x+dx, y, z, x+dx, y+dy, z, x, y+dy, z,
        x, y, z+dz, x+dx, y, z+dz, x+dx, y+dy, z+dz, x, y+dy, z+dz,
    ]
    return {
        "guid": guid,
        "name": "Measured source element",
        "ifc_type": "IfcWall" if guid == "wall" else "IfcPipeSegment",
        "vertices": vertices, "triangles": [0, 1, 2, 0, 2, 3],
    }


def _mesh(box, partial=False):
    return {
        "type": "ifc_true_mesh",
        "geometry_source": "actual_ifc_product_tessellation",
        "schema": "IFC4",
        "elements": [box],
        "partial_model": partial,
    }


def _screen(one, two):
    return screen_ifc_mesh_overlap(
        one, two, primary_file_id=FIRST, secondary_file_id=SECOND,
        primary_sha256="a" * 64, secondary_sha256="b" * 64,
    )


def test_real_3d_tessellation_bounds_produce_unconfirmed_candidate():
    one = _mesh(_box((0, 0, 0), (2, 1, 3), "wall"))
    two = _mesh(_box((1, 0.5, 1), (1, 1, 1), "pipe"))
    report = _screen(one, two)
    assert report["method"] == "ifc_world_coordinate_aabb_broad_phase_v1"
    assert report["candidate_count"] == 1
    candidate = report["candidates"][0]
    assert candidate["classification"] == "potential_spatial_overlap_unverified"
    assert candidate["overlap_min"] == [1, 0.5, 1]
    assert candidate["overlap_max"] == [2, 1, 2]
    assert candidate["source"]["guid"] == "wall"
    assert candidate["target"]["guid"] == "pipe"
    assert report["hard_clashes_confirmed"] == 0
    assert report["full_federation_or_clearance_checks_performed"] is False
    assert report["requires_professional_review"] is True


@pytest.mark.parametrize("location", [(2, 0, 0), (10, 0, 0)])
def test_touching_and_disjoint_geometry_never_generate_volume_overlap(location):
    assert _screen(
        _mesh(_box((0, 0, 0), (2, 2, 2), "wall")),
        _mesh(_box(location, (1, 1, 1), "pipe")),
    )["candidate_count"] == 0


def test_partial_tessellation_blocks_any_fully_clear_claim():
    report = _screen(
        _mesh(_box((0, 0, 0), (1, 1, 1), "wall"), partial=True),
        _mesh(_box((10, 0, 0), (1, 1, 1), "pipe")),
    )
    assert report["candidate_count"] == 0
    assert report["analysis_partial"] is True
    assert report["coordinate_alignment"].endswith("_not_verified")


@pytest.mark.parametrize("bad_vertex", [inf, float("nan"), "bad"])
def test_invalid_coordinates_refused(bad_vertex):
    source = _mesh(_box((0, 0, 0), (1, 1, 1), "wall"))
    source["elements"][0]["vertices"][0] = bad_vertex
    with pytest.raises(ValueError):
        _screen(source, _mesh(_box((0, 0, 0), (1, 1, 1), "pipe")))


def test_metadata_only_or_fabricated_shapes_are_rejected():
    source = _mesh(_box((0, 0, 0), (1, 1, 1), "wall"))
    source["geometry_source"] = "fake_bounding_boxes"
    with pytest.raises(ValueError):
        _screen(source, _mesh(_box((0, 0, 0), (1, 1, 1), "pipe")))


@pytest.mark.asyncio
async def test_saves_verified_same_project_results():
    first = _mesh(_box((0, 0, 0), (1, 1, 1), "wall"))
    second = _mesh(_box((0.5, 0, 0), (1, 1, 1), "pipe"))
    stored = [
        {"project_id": PROJECT, "mesh": first, "source_sha256": "a" * 64},
        {"project_id": PROJECT, "mesh": second, "source_sha256": "b" * 64},
    ]
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{"id": "stored-1"}])
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch.object(routes, "get_project", AsyncMock(
            return_value={"id": PROJECT, "workspace_id": None}
        )),
        patch.object(routes, "get_file", AsyncMock(
            return_value={"project_id": PROJECT, "file_type": "ifc"}
        )),
        patch.object(routes, "get_model_mesh", AsyncMock(side_effect=stored)),
        patch.object(routes, "run_in_threadpool", inline),
        patch.object(routes, "db", db),
    ):
        result = await routes.screen_project_ifc_spatial_overlap(
            UUID(PROJECT), routes.SpatialScreenRequest(
                primary_file_id=UUID(FIRST),
                secondary_file_id=UUID(SECOND),
                same_origin_axes_and_scale_confirmed=True,
            ), user=USER,
        )
    assert result["id"] == "stored-1"
    saved = query.insert.call_args.args[0]
    assert saved["created_by"] == USER["user_id"]
    assert saved["result"]["candidate_count"] == 1
    assert saved["alignment_user_asserted"] is True


@pytest.mark.asyncio
async def test_rejects_missing_alignment_confirmation_before_database_access():
    with patch.object(routes, "get_project", AsyncMock()) as get_project:
        with pytest.raises(HTTPException) as error:
            await routes.screen_project_ifc_spatial_overlap(
                UUID(PROJECT), routes.SpatialScreenRequest(
                    primary_file_id=UUID(FIRST), secondary_file_id=UUID(SECOND)
                ), user=USER,
            )
    assert error.value.status_code == 422
    get_project.assert_not_awaited()


@pytest.mark.asyncio
async def test_foreign_project_ifc_is_rejected_before_geometry_processing():
    with (
        patch.object(routes, "get_project", AsyncMock(
            return_value={"id": PROJECT, "workspace_id": None}
        )),
        patch.object(routes, "get_file", AsyncMock(
            return_value={"project_id": "00000000-0000-0000-0000-000000000099",
                          "file_type": "ifc"}
        )),
        patch.object(routes, "get_model_mesh", AsyncMock()) as mesh,
    ):
        with pytest.raises(HTTPException) as error:
            await routes.screen_project_ifc_spatial_overlap(
                UUID(PROJECT), routes.SpatialScreenRequest(
                    primary_file_id=UUID(FIRST), secondary_file_id=UUID(SECOND),
                    same_origin_axes_and_scale_confirmed=True,
                ), user=USER,
            )
    assert error.value.status_code == 404
    mesh.assert_not_awaited()


@pytest.mark.asyncio
async def test_sovereign_projects_refuse_global_geometry_processing():
    with (
        patch.object(routes, "get_project", AsyncMock(return_value={
            "id": PROJECT, "workspace_id": "sovereign-org"
        })),
        patch.object(routes, "get_file", AsyncMock()) as file,
    ):
        with pytest.raises(HTTPException) as error:
            await routes.screen_project_ifc_spatial_overlap(
                UUID(PROJECT), routes.SpatialScreenRequest(
                    primary_file_id=UUID(FIRST), secondary_file_id=UUID(SECOND),
                    same_origin_axes_and_scale_confirmed=True,
                ), user=USER,
            )
    assert error.value.status_code == 503
    file.assert_not_awaited()
