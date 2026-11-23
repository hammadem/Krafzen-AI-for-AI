"""True metric DXF modelspace dimensions, openings and persistence regression tests."""
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import ezdxf
from fastapi import HTTPException
import pytest

from app.routes import cad_generation_routes as routes
from app.services.parametric_cad_service import build_room_dxf

PROJECT = "00000000-0000-0000-0000-000000000002"
JOB = "00000000-0000-0000-0000-000000000003"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


def sample():
    return {
        "name": "Accessible kitchen",
        "width_m": 4.0, "length_m": 3.0,
        "wall_thickness_m": 0.2,
        "openings": [
            {"kind": "door", "side": "south", "offset_m": 1.0, "clear_width_m": 0.9},
            {"kind": "window", "side": "east", "offset_m": 1.0, "clear_width_m": 0.8},
        ],
    }


def request():
    return routes.RoomRequest(
        project_id=UUID(PROJECT), job_id=UUID(JOB),
        room_name="Accessible kitchen",
        exterior_width_m=4.0, exterior_length_m=3.0,
        wall_thickness_m=0.2,
        openings=[
            routes.OpeningRequest(kind="door", side="south", offset_m=1.0, clear_width_m=0.9),
            routes.OpeningRequest(kind="window", side="east", offset_m=1.0, clear_width_m=0.8),
        ],
    )


def test_generated_dxf_contains_real_metric_dimensions_and_labeled_openings():
    content, meta = build_room_dxf(**sample())
    doc = ezdxf.read(StringIO(content.decode("utf-8")))
    assert doc.header["$INSUNITS"] == 6
    assert doc.header["$MEASUREMENT"] == 1
    assert doc.layers.has_entry("WALLS")
    assert doc.layers.has_entry("DOORS")
    assert doc.layers.has_entry("WINDOWS")
    assert len(doc.modelspace().query("DIMENSION")) == 2
    assert len(doc.modelspace().query('LINE[layer=="WALLS"]')) >= 8
    assert len(doc.modelspace().query('LINE[layer=="JAMBS"]')) == 4
    assert meta["exterior_width_m"] == 4.0
    assert meta["exterior_length_m"] == 3.0
    assert meta["interior_clear_area_m2"] == pytest.approx(9.36)
    assert meta["engineering_accuracy_verified"] is False
    assert meta["requires_professional_review"] is True


@pytest.mark.parametrize("change", [
    {"width_m": float("nan")},
    {"length_m": -1},
    {"wall_thickness_m": 1.8},
    {"name": ""},
    {"openings": [{"kind": "door", "side": "north", "offset_m": 0.1, "clear_width_m": 1.2}]},
    {"openings": [{"kind": "door", "side": "south", "offset_m": 1.0, "clear_width_m": 100.0}]},
    {"openings": [
        {"kind": "door", "side": "south", "offset_m": 1.0, "clear_width_m": 1.0},
        {"kind": "window", "side": "south", "offset_m": 1.8, "clear_width_m": 0.6},
    ]},
])
def test_invalid_or_unmeasured_room_inputs_fail_before_generation(change):
    with pytest.raises(ValueError):
        build_room_dxf(**{**sample(), **change})


@pytest.mark.asyncio
async def test_owned_project_room_generation_saves_real_dxf_file():
    client = MagicMock()

    async def inline(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    async def save_record(data, user):
        assert data["job_id"] == JOB
        assert data["project_id"] == PROJECT
        assert data["file_type"] == "dxf"
        assert data["import_metadata"]["generation_method"] == "parametric_room_v1"
        assert data["path"].startswith(f"{USER['user_id']}/{PROJECT}/generated/{JOB}/")
        assert data["size_bytes"] > 100
        assert user == USER
        return {"id": "saved-1", **data}

    with (
        patch.object(routes, "get_job",
                     AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(routes, "get_project",
                     AsyncMock(return_value={"id": PROJECT, "workspace_id": None})),
        patch.object(routes, "run_in_threadpool", inline),
        patch.object(routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(routes, "create_file", side_effect=save_record),
        patch.object(routes, "record_audit_event", AsyncMock()),
    ):
        result = await routes.create_parametric_room_drawing(
            request(), user=USER,
        )
    assert result["file"]["id"] == "saved-1"
    assert result["geometry"]["interior_clear_area_m2"] == pytest.approx(9.36)
    raw = client.storage.from_.return_value.upload.call_args.kwargs["file"]
    assert ezdxf.read(StringIO(raw.decode())).header["$INSUNITS"] == 6


@pytest.mark.asyncio
async def test_generated_room_rejects_foreign_project_before_storage():
    with (
        patch.object(routes, "get_job",
                     AsyncMock(return_value={"project_id": "00000000-0000-0000-0000-000000000099"})),
        patch.object(routes, "get_project", AsyncMock()) as project,
        patch.object(routes.storage_service, "resolve_target_bucket_and_client") as storage,
    ):
        with pytest.raises(HTTPException) as exc:
            await routes.create_parametric_room_drawing(request(), user=USER)
    assert exc.value.status_code == 404
    project.assert_not_awaited()
    storage.assert_not_called()


@pytest.mark.asyncio
async def test_generated_room_rejects_sovereign_project():
    with (
        patch.object(routes, "get_job",
                     AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(routes, "get_project",
                     AsyncMock(return_value={"workspace_id": "org-uuid"})),
        patch.object(routes.storage_service, "resolve_target_bucket_and_client") as storage,
    ):
        with pytest.raises(HTTPException) as exc:
            await routes.create_parametric_room_drawing(request(), user=USER)
    assert exc.value.status_code == 503
    storage.assert_not_called()


@pytest.mark.asyncio
async def test_failed_drawing_persistence_removes_private_storage_object():
    client = MagicMock()

    async def inline(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch.object(routes, "get_job",
                     AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(routes, "get_project",
                     AsyncMock(return_value={"id": PROJECT, "workspace_id": None})),
        patch.object(routes, "run_in_threadpool", inline),
        patch.object(routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(routes, "create_file", AsyncMock(return_value={"error": "DB unavailable"})),
    ):
        with pytest.raises(HTTPException) as err:
            await routes.create_parametric_room_drawing(request(), user=USER)
    assert err.value.status_code == 503
    client.storage.from_.return_value.remove.assert_called_once()
