"""Regression tests: never return dummy DXF/DWG/IFC export artifacts."""

import pytest

from app.services.export_pipeline_service import (
    ExportGenerationUnavailableError,
    run_export_generation,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("export_format", ["dxf", "dwg", "ifc"])
async def test_unimplemented_formats_fail_instead_of_producing_fake_artifacts(export_format):
    job = {"id": "export-1", "project_id": "project-1", "format": export_format}

    with pytest.raises(ExportGenerationUnavailableError, match="actual project data"):
        await run_export_generation(job)

    assert "artifact_file_id" not in job
    assert "artifact_url" not in job


@pytest.mark.asyncio
async def test_export_generation_requires_a_project():
    with pytest.raises(ValueError, match="project_id"):
        await run_export_generation({"format": "dxf"})


@pytest.mark.asyncio
async def test_export_generation_rejects_unknown_formats():
    with pytest.raises(ValueError, match="Unsupported export format"):
        await run_export_generation({"project_id": "project-1", "format": "not-a-format"})
