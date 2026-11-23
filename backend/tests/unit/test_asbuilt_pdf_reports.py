"""Actual source-derived as-built PDF and project-ownership export tests."""
from io import StringIO
from unittest.mock import AsyncMock, patch
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
COMPARISON = "00000000-0000-0000-0000-000000000005"


def _dxf(y: float) -> bytes:
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # millimetres
    model = doc.modelspace()
    model.add_line((0, 0), (2500, 0), dxfattribs={"layer": "A-WALL"})
    model.add_line((0, y), (1000, y), dxfattribs={"layer": "A-WALL"})
    writer = StringIO()
    doc.write(writer)
    return writer.getvalue().encode()


def _saved_record() -> dict:
    result = compare_dxf_bytes(_dxf(1000), _dxf(1300))
    assert result["added_count"] == result["removed_count"] == 1
    return {
        "id": COMPARISON, "project_id": PROJECT,
        "original_file_id": ORIGINAL, "revised_file_id": REVISED,
        "created_by": USER["user_id"],
        "created_at": "2026-11-24T10:00:00+00:00",
        "result": result,
    }


def test_saved_real_dxf_comparison_generates_pdf_without_dummy_values():
    record = _saved_record()
    pdf = generate_asbuilt_comparison_pdf(record)
    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf[-50:]
    assert 1000 < len(pdf) < 5 * 1024 * 1024
    assert record["result"]["requires_professional_review"] is True


@pytest.mark.parametrize("corruption", [
    lambda row: row["result"].update(added_count=5),
    lambda row: row["result"].update(source_hash_sha256="not-a-hash"),
    lambda row: row["result"].update(method="generic_ai_summary"),
    lambda row: row["result"].update(requires_professional_review=False),
    lambda row: row["result"].update(added_samples=[{"entity": "LINE"}]),
    lambda row: row["result"].update(insunits=0),
])
def test_corrupted_or_unverifiable_saved_report_is_rejected(corruption):
    record = _saved_record()
    corruption(record)
    with pytest.raises(ValueError):
        generate_asbuilt_comparison_pdf(record)


@pytest.mark.asyncio
async def test_download_pdf_reuses_owned_saved_record_and_sends_pdf():
    record = _saved_record()

    async def inline(fn, *args):
        return fn(*args)

    with (
        patch.object(
            asbuilt_routes, "read_saved_comparison",
            AsyncMock(return_value=record),
        ) as owned,
        patch.object(asbuilt_routes, "run_in_threadpool", inline),
    ):
        response = await asbuilt_routes.download_saved_comparison_pdf(
            UUID(COMPARISON), user=USER
        )
    owned.assert_awaited_once_with(UUID(COMPARISON), user=USER)
    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF-")
    assert response.headers["cache-control"] == "no-store"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_pdf_export_never_renders_another_users_comparison():
    with (
        patch.object(
            asbuilt_routes, "read_saved_comparison",
            AsyncMock(side_effect=HTTPException(status_code=404, detail="Not found"))
        ),
        patch.object(asbuilt_routes, "generate_asbuilt_comparison_pdf") as render,
    ):
        with pytest.raises(HTTPException) as exc:
            await asbuilt_routes.download_saved_comparison_pdf(
                UUID(COMPARISON), user=USER
            )
    assert exc.value.status_code == 404
    render.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_stored_result_returns_409_not_a_pdf():
    record = _saved_record()
    record["result"]["added_count"] = 123

    async def inline(fn, *args):
        return fn(*args)

    with (
        patch.object(
            asbuilt_routes, "read_saved_comparison", AsyncMock(return_value=record)
        ),
        patch.object(asbuilt_routes, "run_in_threadpool", inline),
    ):
        with pytest.raises(HTTPException) as exc:
            await asbuilt_routes.download_saved_comparison_pdf(
                UUID(COMPARISON), user=USER
            )
    assert exc.value.status_code == 409
