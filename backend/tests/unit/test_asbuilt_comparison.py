"""Real DXF geometry assertions and HTTP contract tests for as-built comparisons."""
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import ezdxf
import pytest
from fastapi import HTTPException

from app.services.asbuilt_service import compare_dxf_bytes
from app.routes import asbuilt_routes

PROJECT = "00000000-0000-0000-0000-000000000002"
OLD = "00000000-0000-0000-0000-000000000003"
NEW = "00000000-0000-0000-0000-000000000004"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


def drawing(lines, units=4, add_text=False):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = units
    space = doc.modelspace()
    for start, end in lines:
        space.add_line(start, end, dxfattribs={"layer": "WALLS"})
    if add_text:
        space.add_text("note", dxfattribs={"layer": "NOTES"})
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


def test_real_dxf_additions_removals_are_deterministic():
    a = drawing([((0, 0), (10, 0)), ((0, 2), (3, 2))])
    b = drawing([((0, 0), (10, 0)), ((0, 3), (5, 3))])
    report = compare_dxf_bytes(a, b)
    assert report["method"] == "exact_coordinate_entity_diff_v1"
    assert report["insunits"] == 4
    assert report["unchanged_count"] == 1
    assert report["added_count"] == 1
    assert report["removed_count"] == 1
    assert report["comparison_complete"] is True
    assert report["source_hash_sha256"] != report["revised_hash_sha256"]
    assert report["requires_professional_review"] is True


def test_unchanged_line_endpoint_order_does_not_generate_changes():
    a = drawing([((0, 0), (10, 0))])
    b = drawing([((10, 0), (0, 0))])
    report = compare_dxf_bytes(a, b)
    assert report["added_count"] == report["removed_count"] == 0
    assert report["unchanged_count"] == 1


def test_unsupported_entities_are_explicit_and_not_claimed_as_compared():
    a = drawing([((0, 0), (10, 0))], add_text=True)
    b = drawing([((0, 0), (10, 0))], add_text=True)
    report = compare_dxf_bytes(a, b)
    assert report["comparison_complete"] is False
    assert report["unsupported_original"]["TEXT"] == 1


@pytest.mark.parametrize("invalid", [b"", b"\x00\x01not dxf"])
def test_bad_dxf_rejected(invalid):
    with pytest.raises(ValueError):
        compare_dxf_bytes(invalid, drawing([((0, 0), (1, 0))]))


@pytest.mark.parametrize("old_units,new_units", [(0, 4), (4, 0), (1, 4)])
def test_unitless_or_mismatched_units_rejected(old_units, new_units):
    with pytest.raises(ValueError, match="INSUNITS"):
        compare_dxf_bytes(
            drawing([((0, 0), (1, 0))], units=old_units),
            drawing([((0, 0), (1, 0))], units=new_units),
        )


@pytest.mark.asyncio
async def test_comparison_persisted_with_verified_file_ids():
    raw = drawing([((0, 0), (10, 0))])
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{
        "id": "saved-report-1", "project_id": PROJECT, "result": {"added_count": 0}
    }])
    client = MagicMock()
    client.table.return_value = query

    async def inline(fn, *args):
        return fn(*args)

    with (
        patch.object(asbuilt_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(asbuilt_routes, "_read_dxf", AsyncMock(return_value=raw)),
        patch.object(asbuilt_routes, "db", client),
        patch.object(asbuilt_routes, "run_in_threadpool", inline),
    ):
        result = await asbuilt_routes.compare_project_drawings(
            asbuilt_routes.CompareRequest(
                project_id=UUID(PROJECT), original_file_id=UUID(OLD), revised_file_id=UUID(NEW)
            ),
            user=USER,
        )
    assert result["id"] == "saved-report-1"
    row = query.insert.call_args.args[0]
    assert row["project_id"] == PROJECT
    assert row["original_file_id"] == OLD
    assert row["revised_file_id"] == NEW
    assert row["created_by"] == USER["user_id"]
    assert row["result"]["method"] == "exact_coordinate_entity_diff_v1"


@pytest.mark.asyncio
async def test_file_reads_reject_cross_project_and_untrusted_path_before_storage():
    with patch.object(
        asbuilt_routes, "get_file",
        AsyncMock(return_value={
            "id": OLD, "project_id": PROJECT, "file_type": "dxf",
            "bucket": "dxf-files", "path": "../../otheruser/data.dxf",
        }),
    ), patch.object(
        asbuilt_routes.storage_service,
        "resolve_target_bucket_and_client",
        return_value=(MagicMock(), "dxf-files", "global"),
    ) as resolve:
        with pytest.raises(HTTPException) as err:
            await asbuilt_routes._read_dxf(OLD, PROJECT, USER)
    assert err.value.status_code == 409
    resolve.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_organization_comparison_fails_closed():
    with patch.object(
        asbuilt_routes, "get_project", AsyncMock(return_value={
            "id": PROJECT, "workspace_id": "00000000-0000-0000-0000-000000000009"
        }),
    ):
        with pytest.raises(HTTPException) as err:
            await asbuilt_routes._owned_project(PROJECT, USER)
    assert err.value.status_code == 503


def test_asbuilt_endpoint_is_registered_and_paid_gated(client):
    response = client.post("/api/v1/asbuilt/compare", json={
        "project_id": PROJECT, "original_file_id": OLD, "revised_file_id": OLD
    })
    assert response.status_code == 422
    assert "different" in response.text


@pytest.mark.asyncio
async def test_persistence_failure_is_not_reported_as_success():
    raw = drawing([((0, 0), (10, 0))])
    client = MagicMock()
    query = MagicMock()
    query.insert.return_value = query
    query.execute.side_effect = RuntimeError("database down")
    client.table.return_value = query

    async def inline(fn, *args):
        return fn(*args)

    with (
        patch.object(asbuilt_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(asbuilt_routes, "_read_dxf", AsyncMock(return_value=raw)),
        patch.object(asbuilt_routes, "db", client),
        patch.object(asbuilt_routes, "run_in_threadpool", inline),
    ):
        with pytest.raises(HTTPException) as err:
            await asbuilt_routes.compare_project_drawings(
                asbuilt_routes.CompareRequest(
                    project_id=UUID(PROJECT), original_file_id=UUID(OLD),
                    revised_file_id=UUID(NEW)
                ),
                user=USER,
            )
    assert err.value.status_code == 503


def _drawing_with_extrusion(kind, extrusion=(0, 0, 1), thickness=0):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    model = doc.modelspace()
    attribs = {"extrusion": extrusion, "thickness": thickness}
    if kind == "CIRCLE":
        model.add_circle((2, 3, 0), 1, dxfattribs=attribs)
    elif kind == "ARC":
        model.add_arc((2, 3, 0), 1, 0, 90, dxfattribs=attribs)
    elif kind == "LWPOLYLINE":
        model.add_lwpolyline([(0, 0), (1, 1)], dxfattribs=attribs)
    else:
        model.add_line((0, 0), (1, 1), dxfattribs=attribs)
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue().encode()


@pytest.mark.parametrize("kind", ["CIRCLE", "ARC", "LWPOLYLINE"])
def test_nonstandard_object_coordinates_are_not_claimed_as_equivalent(kind):
    original = _drawing_with_extrusion(kind)
    revised = _drawing_with_extrusion(kind, extrusion=(0, 1, 0))
    report = compare_dxf_bytes(original, revised)
    assert report["comparison_complete"] is False
    assert report["unchanged_count"] == 0
    assert report["unsupported_revised"][kind + ":nonstandard_ocs"] == 1
    assert report["revised_supported_count"] == 0


def test_thickness_geometry_is_explicitly_unassessed():
    report = compare_dxf_bytes(
        _drawing_with_extrusion("LINE"),
        _drawing_with_extrusion("LINE", thickness=2),
    )
    assert report["comparison_complete"] is False
    assert report["unsupported_revised"]["LINE:nonzero_thickness"] == 1
    assert report["unchanged_count"] == 0
