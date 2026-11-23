"""Real export pipeline regression tests; no live storage or ODA required."""

import base64
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import ezdxf
import pytest

from app.schemas.export_contracts import PipelineStage
from app.services import export_pipeline_service as pipeline

PROJECT_ID = "bbbbbbbb-0000-0000-0000-000000000002"
USER_ID = "cccccccc-0000-0000-0000-000000000003"
JOB_ID = "aaaaaaaa-0000-0000-0000-000000000001"
SOURCE = "data:image/png;base64," + base64.b64encode(b"stored-image").decode()
PROJECT = {
    "id": PROJECT_ID, "user_id": USER_ID,
    "image_url": SOURCE, "workspace_id": None,
}
JOB = {"id": JOB_ID, "project_id": PROJECT_ID, "requested_by": USER_ID,
       "region_code": "global", "format": "dxf", "metadata": {"idempotency_key": "unique"}}


def write_dxf(path: Path, *, with_entity=True):
    doc = ezdxf.new("R2010")
    if with_entity:
        doc.modelspace().add_line((0, 0), (10, 10))
    doc.saveas(path)


@pytest.mark.asyncio
async def test_dxf_export_uses_generated_project_vector_and_persists_artifact(tmp_path):
    path = tmp_path / "output.dxf"
    write_dxf(path)
    saved = {"artifact_file_id": "file-123"}
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value=PROJECT)),
        patch.object(pipeline.local_dxf_service, "convert_to_dxf", AsyncMock(return_value=str(path))) as convert,
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock(return_value="https://storage.example/file")) as upload,
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client", return_value=(object(), "dxf-files", "global")),
        patch.object(pipeline, "create_artifact_file", AsyncMock(return_value={"id": "file-123"})) as create,
        patch.object(pipeline, "update_export_status", AsyncMock(return_value=saved)) as persist,
    ):
        job = JOB.copy()
        result = await pipeline.run_export_generation(job)

    convert.assert_awaited_once_with(SOURCE)
    upload.assert_awaited_once()
    uploaded = upload.await_args.kwargs["file_bytes"]
    assert uploaded.startswith(b"  0") or b"SECTION" in uploaded
    assert len(uploaded) > 100
    assert result["artifact_file_id"] == "file-123"
    assert result["generation_method"] == "raster_vector_trace"
    assert job["artifact_file_id"] == "file-123"
    assert job["metadata"]["stage"] == PipelineStage.ARTIFACT_STORAGE.value
    assert create.await_args.kwargs["file_data"]["size_bytes"] == len(uploaded)
    assert persist.await_args.args[1]["file_path"].endswith(".dxf")
    assert not path.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("format", ["ifc", "revit_package", ""])
async def test_unsupported_formats_fail_without_upload(format):
    with patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock()) as upload:
        with pytest.raises(RuntimeError, match="no implemented generator"):
            await pipeline.run_export_generation({**JOB, "format": format})
    upload.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_project_image_fails_without_upload():
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value={**PROJECT, "image_url": None})),
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock()) as upload,
    ):
        with pytest.raises(RuntimeError, match="no supported stored image"):
            await pipeline.run_export_generation(JOB.copy())
    upload.assert_not_awaited()


@pytest.mark.asyncio
async def test_untrusted_remote_project_image_is_rejected():
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value={**PROJECT, "image_url": "http://127.0.0.1/latest/meta-data"})),
        patch.object(pipeline.local_dxf_service, "convert_to_dxf", AsyncMock()) as converter,
    ):
        with pytest.raises(RuntimeError, match="remote image URLs are not fetched"):
            await pipeline.run_export_generation(JOB.copy())
    converter.assert_not_awaited()


@pytest.mark.asyncio
async def test_sovereign_region_export_blocked_until_regional_metadata_is_ready():
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock()) as project,
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock()) as upload,
    ):
        with pytest.raises(RuntimeError, match="Sovereign exports are unavailable"):
            await pipeline.run_export_generation({**JOB, "region_code": "us", "organization_id": "77777777-0000-0000-0000-000000000001"})
    project.assert_not_awaited()
    upload.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_dxf_output_rejected_before_storage(tmp_path):
    path = tmp_path / "empty.dxf"
    write_dxf(path, with_entity=False)
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value=PROJECT)),
        patch.object(pipeline.local_dxf_service, "convert_to_dxf", AsyncMock(return_value=str(path))),
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock()) as upload,
    ):
        with pytest.raises(RuntimeError, match="no drawable entities"):
            await pipeline.run_export_generation(JOB.copy())
    upload.assert_not_awaited()
    assert not path.exists()


@pytest.mark.asyncio
async def test_upload_failure_never_creates_artifact_record(tmp_path):
    path = tmp_path / "valid.dxf"
    write_dxf(path)
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value=PROJECT)),
        patch.object(pipeline.local_dxf_service, "convert_to_dxf", AsyncMock(return_value=str(path))),
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock(return_value=None)),
        patch.object(pipeline, "create_artifact_file", AsyncMock()) as create,
    ):
        with pytest.raises(RuntimeError, match="upload did not return"):
            await pipeline.run_export_generation(JOB.copy())
    create.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_persisted_artifact_reference_is_failure(tmp_path):
    path = tmp_path / "valid.dxf"
    write_dxf(path)
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value=PROJECT)),
        patch.object(pipeline.local_dxf_service, "convert_to_dxf", AsyncMock(return_value=str(path))),
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock(return_value="https://storage.example")),
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client", return_value=(object(), "dxf-files", "global")),
        patch.object(pipeline, "create_artifact_file", AsyncMock(return_value={"id": "file-123"})),
        patch.object(pipeline, "update_export_status", AsyncMock(return_value={"artifact_file_id": None})),
    ):
        with pytest.raises(RuntimeError, match="reference was not persisted"):
            await pipeline.run_export_generation(JOB.copy())


@pytest.mark.asyncio
async def test_dwg_requires_valid_converter_output(tmp_path):
    path = tmp_path / "valid.dxf"
    write_dxf(path)
    dwg_path = tmp_path / "invalid.dwg"
    dwg_path.write_bytes(b"not a real drawing")
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value=PROJECT)),
        patch.object(pipeline.local_dxf_service, "convert_to_dxf", AsyncMock(return_value=str(path))),
        patch.object(pipeline.dwg_converter_service, "convert_dxf_path_to_dwg", return_value=SimpleNamespace(dwg_path=str(dwg_path), work_dir=str(tmp_path / "oda"))),
        patch.object(pipeline.storage_service, "upload_cad_file", AsyncMock()) as upload,
    ):
        with pytest.raises(RuntimeError, match="valid AutoCAD header"):
            await pipeline.run_export_generation({**JOB, "format": "dwg"})
    upload.assert_not_awaited()


@pytest.mark.asyncio
async def test_project_loader_checks_owner():
    result = SimpleNamespace(data={**PROJECT, "user_id": "somebody-else"})
    query = SimpleNamespace(
        select=lambda *_: None,
    )
    class StubQuery:
        def select(self, *_): return self
        def eq(self, *_): return self
        def maybe_single(self): return self
        def execute(self): return result
    class StubClient:
        def table(self, *_): return StubQuery()
    with patch.object(pipeline, "db", StubClient()):
        with pytest.raises(PermissionError, match="does not own"):
            await pipeline._load_source_project(PROJECT_ID, USER_ID)
