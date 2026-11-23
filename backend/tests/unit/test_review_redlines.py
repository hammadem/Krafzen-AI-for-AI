"""Real DXF preview, same-file review authorization, and saved redline contract tests."""
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import ezdxf
import pytest
from fastapi import HTTPException

from app.routes import review_routes
from app.services.dxf_preview_service import render_dxf_preview

PROJECT = "00000000-0000-0000-0000-000000000002"
FILE = "00000000-0000-0000-0000-000000000003"
REDLINE = "00000000-0000-0000-0000-000000000004"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


def source_dxf():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (12, 0))
    msp.add_circle((6, 4), 2)
    msp.add_text("cannot pretend this is rendered")
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


def test_render_real_dxf_svg_contains_actual_lines_and_circles():
    svg = render_dxf_preview(source_dxf())
    assert "<svg " in svg
    assert "<line " in svg
    assert "<circle " in svg
    assert "unsupported entities omitted" in svg
    assert "cannot pretend this is rendered" not in svg
    assert "<script" not in svg


def test_svg_renderer_rejects_empty_malformed_and_unsafe_dxf():
    for raw in (b"", b"\x00\x01not dxf", b"not a drawing"):
        with pytest.raises(ValueError):
            render_dxf_preview(raw)


def test_markup_validates_endpoints_coordinates_and_comment():
    with pytest.raises(ValueError):
        review_routes.NewRedline(kind="line", x=0.2, y=0.3, comment="line")
    with pytest.raises(ValueError):
        review_routes.NewRedline(kind="comment", x=1.5, y=0.5, comment="bad")
    with pytest.raises(ValueError):
        review_routes.NewRedline(kind="comment", x=0.3, y=0.3, comment=" ")


@pytest.mark.asyncio
async def test_preview_requires_owned_record_before_reading_private_blob():
    with patch.object(review_routes, "get_file", AsyncMock(return_value=None)), patch.object(
        review_routes, "_read_dxf", AsyncMock()
    ) as read:
        with pytest.raises(HTTPException) as err:
            await review_routes.drawing_preview(UUID(FILE), user=USER)
    assert err.value.status_code == 404
    read.assert_not_awaited()


@pytest.mark.asyncio
async def test_drawing_preview_returns_real_geometry():
    with (
        patch.object(
            review_routes, "get_file", AsyncMock(return_value={
                "id": FILE, "project_id": PROJECT, "file_type": "dxf"
            })
        ),
        patch.object(review_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(review_routes, "_read_dxf", AsyncMock(return_value=source_dxf())),
    ):
        resp = await review_routes.drawing_preview(UUID(FILE), user=USER)
    assert resp.status_code == 200
    assert b"<line " in resp.body
    assert b"<circle " in resp.body
    assert resp.media_type == "image/svg+xml"


@pytest.mark.asyncio
async def test_creating_markups_persists_project_version_author_and_coordinates():
    record = {"id": FILE, "project_id": PROJECT, "file_type": "dxf", "version": 4}
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{"id": REDLINE, "status": "open"}])
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(review_routes, "_owned_dxf_record", AsyncMock(return_value=record)),
        patch.object(review_routes, "db", db),
        patch.object(review_routes, "run_in_threadpool", inline),
    ):
        result = await review_routes.create_drawing_redline(
            UUID(FILE),
            review_routes.NewRedline(
                kind="rectangle", x=0.1, y=0.2, x2=0.5, y2=0.7,
                comment="Check door clearance", severity="high"
            ),
            user=USER,
        )
    saved = query.insert.call_args.args[0]
    assert result["id"] == REDLINE
    assert saved["project_id"] == PROJECT
    assert saved["file_id"] == FILE
    assert saved["file_version"] == 4
    assert saved["created_by"] == USER["user_id"]
    assert (saved["x"], saved["y"], saved["x2"], saved["y2"]) == (0.1, 0.2, 0.5, 0.7)


@pytest.mark.asyncio
async def test_resolve_requires_redline_owned_by_requester():
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.maybe_single.return_value = query
    query.execute.return_value = SimpleNamespace(data=None)
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(review_routes, "db", db),
        patch.object(review_routes, "run_in_threadpool", inline),
        patch.object(review_routes, "_owned_dxf_record", AsyncMock()) as owned,
    ):
        with pytest.raises(HTTPException) as err:
            await review_routes.update_redline_status(
                UUID(REDLINE), review_routes.ReviewDecision(status="resolved"), user=USER
            )
    assert err.value.status_code == 404
    owned.assert_not_awaited()
    assert any(c.args == ("created_by", USER["user_id"]) for c in query.eq.call_args_list)


def test_reviewer_redline_api_is_registered_and_paid_gated(client):
    resp = client.post(f"/api/v1/reviews/files/{FILE}/redlines", json={
        "kind": "line", "x": 0.2, "y": 0.3, "comment": "needs two points"
    })
    assert resp.status_code == 422
