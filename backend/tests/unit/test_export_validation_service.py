"""Tests for export validation preflight/postflight framework."""

import pytest

from app.services.export_validation_service import run_postflight, run_preflight


@pytest.mark.asyncio
async def test_preflight_blocks_missing_project():
    report = await run_preflight({})
    assert report.can_proceed is False
    assert any(i.code == "EXPORT_MISSING_PROJECT" for i in report.issues)


@pytest.mark.asyncio
async def test_preflight_passes_minimal_job():
    report = await run_preflight(
        {"id": "job-1", "project_id": "proj-1", "format": "dxf", "metadata": {"idempotency_key": "abc12345"}}
    )
    assert report.can_proceed is True


@pytest.mark.asyncio
async def test_postflight_fails_without_required_artifact():
    report = await run_postflight({"id": "exp-1", "project_id": "p1", "format": "dxf"})
    assert report.passed is False
    assert report.requires_review is False
    assert any(i.code == "EXPORT_MISSING_ARTIFACT" for i in report.issues)


@pytest.mark.asyncio
async def test_postflight_passes_when_artifact_is_linked():
    report = await run_postflight({
        "id": "exp-1",
        "project_id": "p1",
        "format": "dxf",
        "artifact_file_id": "file-1",
    })
    assert report.passed is True
