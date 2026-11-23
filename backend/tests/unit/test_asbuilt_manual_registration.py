"""Source-backed DXF registration / bounded overlay and persistence regressions."""
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import ezdxf
import pytest
from fastapi import HTTPException

from app.routes import asbuilt_routes
from app.services.asbuilt_pdf_service import generate_asbuilt_comparison_pdf
from app.services.asbuilt_service import compare_dxf_bytes


USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
PROJECT = "00000000-0000-0000-0000-000000000002"
ORIGINAL = "00000000-0000-0000-0000-000000000003"
REVISED = "00000000-0000-0000-0000-000000000004"


def _dxf(xoff=0, yoff=0, with_added=False, units=4):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = units
    model = doc.modelspace()
    model.add_line((xoff, yoff), (xoff + 10, yoff), dxfattribs={"layer": "A-WALL"})
    model.add_circle((xoff + 4, yoff + 3), 2, dxfattribs={"layer": "A-CIRCLE"})
    if with_added:
        model.add_line((xoff + 3, yoff + 4), (xoff + 7, yoff + 4),
                       dxfattribs={"layer": "A-WALL"})
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue().encode()


def _alignment():
    return {
        "original": {"x": 0.0, "y": 0.0},
        "revised": {"x": 100.0, "y": -50.0},
        "same_reference_point_confirmed": True,
    }


def test_translation_avoids_fabricated_add_remove_counts():
    original, revised = _dxf(), _dxf(100, -50)
    raw = compare_dxf_bytes(original, revised)
    assert raw["added_count"] == 2 and raw["removed_count"] == 2
    registered = compare_dxf_bytes(original, revised, alignment=_alignment())
    assert registered["method"] == "manual_translation_entity_diff_v2"
    assert registered["alignment"]["revised_translation_xy"] == [-100.0, 50.0]
    assert registered["added_count"] == registered["removed_count"] == 0
    assert registered["unchanged_count"] == 2
    assert registered["source_hash_sha256"] != registered["revised_hash_sha256"]
    assert registered["alignment"]["automatically_verified"] is False
    assert registered["requires_professional_review"] is True
    preview = registered["preview"]
    assert preview["bounds"] is not None
    assert len(preview["groups"]["unchanged"]) == 2
    assert preview["source"] == "real_dxf_modelspace_signatures"


def test_aligned_new_geometry_draws_only_real_added_primitives():
    result = compare_dxf_bytes(_dxf(), _dxf(100, -50, with_added=True),
                               alignment=_alignment())
    assert result["unchanged_count"] == 2
    assert result["added_count"] == 1
    assert result["removed_count"] == 0
    line = result["preview"]["groups"]["added"][0]
    assert line["type"] == "line"
    assert line["x1"] == 3
    assert line["y1"] == 4
    assert line["x2"] == 7
    assert line["y2"] == 4


@pytest.mark.parametrize("bad", [
    {"original": {"x": 0, "y": 0}, "revised": {"x": 100, "y": -50},
     "same_reference_point_confirmed": False},
    {"original": {"x": float("nan"), "y": 0}, "revised": {"x": 100, "y": -50},
     "same_reference_point_confirmed": True},
    {"original": {"x": 0, "y": 0}, "revised": {"x": 100, "y": 1e9},
     "same_reference_point_confirmed": True},
])
def test_unverified_or_nonfinite_alignment_rejected(bad):
    with pytest.raises(ValueError):
        compare_dxf_bytes(_dxf(), _dxf(100, -50), alignment=bad)


def test_manual_registration_never_silently_converts_dxf_units():
    with pytest.raises(ValueError, match="INSUNITS"):
        compare_dxf_bytes(_dxf(units=4), _dxf(100, -50, units=6),
                          alignment=_alignment())


def test_source_bound_manual_registration_pdf_and_tamper_rejection():
    record = {
        "id": "saved-1", "project_id": PROJECT,
        "original_file_id": ORIGINAL, "revised_file_id": REVISED,
        "created_at": "2026-11-24T00:00:00+00:00",
        "result": compare_dxf_bytes(_dxf(), _dxf(100, -50),
                                   alignment=_alignment()),
    }
    pdf = generate_asbuilt_comparison_pdf(record)
    assert pdf.startswith(b"%PDF-")
    record["result"]["alignment"]["revised_translation_xy"] = [1000, 500]
    with pytest.raises(ValueError, match="inconsistent"):
        generate_asbuilt_comparison_pdf(record)


@pytest.mark.asyncio
async def test_registration_payload_is_saved_from_owned_source_dxf():
    raw = _dxf()
    other = _dxf(100, -50)
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{"id": "registered-1"}])
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn, *args):
        return fn(*args)

    with (
        patch.object(asbuilt_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(asbuilt_routes, "_read_dxf", AsyncMock(side_effect=[raw, other])),
        patch.object(asbuilt_routes, "db", db),
        patch.object(asbuilt_routes, "run_in_threadpool", inline),
    ):
        result = await asbuilt_routes.compare_project_drawings(
            asbuilt_routes.CompareRequest(
                project_id=UUID(PROJECT),
                original_file_id=UUID(ORIGINAL),
                revised_file_id=UUID(REVISED),
                alignment=asbuilt_routes.ManualAlignment(
                    original=asbuilt_routes.ReferencePoint(x=0, y=0),
                    revised=asbuilt_routes.ReferencePoint(x=100, y=-50),
                    same_reference_point_confirmed=True,
                ),
            ), user=USER,
        )
    assert result["id"] == "registered-1"
    saved = query.insert.call_args.args[0]
    assert saved["result"]["method"] == "manual_translation_entity_diff_v2"
    assert saved["result"]["unchanged_count"] == 2
    assert saved["project_id"] == PROJECT
    assert saved["created_by"] == USER["user_id"]


@pytest.mark.asyncio
async def test_unconfirmed_reference_fails_before_private_source_reads():
    with (
        patch.object(asbuilt_routes, "_owned_project", AsyncMock()) as project,
        patch.object(asbuilt_routes, "_read_dxf", AsyncMock()) as read,
    ):
        with pytest.raises(HTTPException) as error:
            await asbuilt_routes.compare_project_drawings(
                asbuilt_routes.CompareRequest(
                    project_id=UUID(PROJECT), original_file_id=UUID(ORIGINAL),
                    revised_file_id=UUID(REVISED),
                    alignment=asbuilt_routes.ManualAlignment(
                        original=asbuilt_routes.ReferencePoint(x=0, y=0),
                        revised=asbuilt_routes.ReferencePoint(x=0, y=0),
                        same_reference_point_confirmed=False,
                    ),
                ), user=USER,
            )
    assert error.value.status_code == 422
    project.assert_not_awaited()
    read.assert_not_awaited()
