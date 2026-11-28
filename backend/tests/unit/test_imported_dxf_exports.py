"""Actual imported DXF export preserves original geometry and rejects other tenants."""
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import ezdxf
import pytest

from app.services import export_pipeline_service as pipeline

USER = "00000000-0000-0000-0000-000000000001"
PROJECT = "00000000-0000-0000-0000-000000000002"
SOURCE_JOB = "00000000-0000-0000-0000-000000000003"
SOURCE_FILE = "00000000-0000-0000-0000-000000000004"
EXPORT = "00000000-0000-0000-0000-000000000005"
SOURCE_PATH = f"{USER}/{PROJECT}/imports/{SOURCE_JOB}/import_verified.dxf"


def real_dxf() -> bytes:
    drawing = ezdxf.new("R2010")
    drawing.header["$INSUNITS"] = 4
    drawing.layers.new("DIMENSIONED-WALLS")
    space = drawing.modelspace()
    space.add_line((0, 0), (3600, 0), dxfattribs={"layer": "DIMENSIONED-WALLS"})
    space.add_circle((2000, 1200), 250)
    out = StringIO()
    drawing.write(out)
    return out.getvalue().encode()


def file_row(data: bytes, **overrides):
    return {
        "id": SOURCE_FILE, "job_id": SOURCE_JOB, "project_id": PROJECT,
        "file_type": "dxf", "bucket": "dxf-files", "path": SOURCE_PATH,
        "size_bytes": len(data), "archived_at": None,
        **overrides,
    }


def database(files, project_id=PROJECT):
    db = MagicMock()
    jobs_query = MagicMock()
    files_query = MagicMock()
    for q in (jobs_query, files_query):
        q.select.return_value = q
        q.eq.return_value = q
        q.limit.return_value = q
        q.maybe_single.return_value = q
    jobs_query.execute.return_value = SimpleNamespace(
        data={"project_id": project_id}
    )
    files_query.execute.return_value = SimpleNamespace(data=files)
    db.table.side_effect = lambda name: jobs_query if name == "jobs" else files_query
    return db, jobs_query, files_query


async def inline(fn):
    return fn()


@pytest.mark.asyncio
async def test_scanned_dxf_keeps_exact_bytes_layers_and_units():
    original = real_dxf()
    db, jobs, files = database([file_row(original)])
    client = MagicMock()
    client.storage.from_.return_value.download.return_value = original
    with (
        patch.object(pipeline, "db", db),
        patch.object(pipeline, "run_in_threadpool", inline),
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
    ):
        data, file_id, units = await pipeline._load_imported_dxf(
            {"source_job_id": SOURCE_JOB, "metadata": {"source_file_id": SOURCE_FILE}},
            PROJECT, USER,
        )
    assert data == original
    assert file_id == SOURCE_FILE
    assert units == 4
    stored = ezdxf.read(StringIO(data.decode()))
    assert stored.header["$INSUNITS"] == 4
    assert stored.layers.has_entry("DIMENSIONED-WALLS")
    assert len(stored.modelspace().query("LINE")) == 1
    assert len(stored.modelspace().query("CIRCLE")) == 1
    client.storage.from_.return_value.download.assert_called_once_with(SOURCE_PATH)


@pytest.mark.asyncio
async def test_foreign_source_job_rejected_before_storage():
    data = real_dxf()
    db, _, _ = database([file_row(data)], project_id="00000000-0000-0000-0000-000000000009")
    client = MagicMock()
    with (
        patch.object(pipeline, "db", db),
        patch.object(pipeline, "run_in_threadpool", inline),
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
    ):
        with pytest.raises(PermissionError, match="Source job"):
            await pipeline._load_imported_dxf(
                {"source_job_id": SOURCE_JOB}, PROJECT, USER
            )
    client.storage.from_.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("overrides", [
    {"bucket": "another-tenant"},
    {"project_id": "00000000-0000-0000-0000-000000000009"},
    {"path": "other-account/forged.dxf"},
    {"path": SOURCE_PATH.replace("import_verified.dxf", "../other.dxf")},
    {"archived_at": "2026-11-23T01:00:00Z"},
    {"size_bytes": 0},
])
async def test_untrusted_source_metadata_never_downloaded(overrides):
    data = real_dxf()
    db, _, _ = database([file_row(data, **overrides)])
    client = MagicMock()
    with (
        patch.object(pipeline, "db", db),
        patch.object(pipeline, "run_in_threadpool", inline),
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
    ):
        with pytest.raises((RuntimeError, PermissionError)):
            await pipeline._load_imported_dxf(
                {"source_job_id": SOURCE_JOB}, PROJECT, USER
            )
    client.storage.from_.return_value.download.assert_not_called()


@pytest.mark.asyncio
async def test_multiple_dxf_files_require_explicit_selection():
    raw = real_dxf()
    other_id = "00000000-0000-0000-0000-000000000006"
    db, _, _ = database([file_row(raw), file_row(raw, id=other_id)])
    client = MagicMock()
    with (
        patch.object(pipeline, "db", db),
        patch.object(pipeline, "run_in_threadpool", inline),
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
    ):
        with pytest.raises(RuntimeError, match="unambiguous"):
            await pipeline._load_imported_dxf(
                {"source_job_id": SOURCE_JOB}, PROJECT, USER
            )
    client.storage.from_.return_value.download.assert_not_called()


@pytest.mark.asyncio
async def test_imported_dxf_produces_real_downloadable_export_and_provenance():
    raw = real_dxf()
    job = {
        "id": EXPORT, "source_job_id": SOURCE_JOB, "project_id": PROJECT,
        "requested_by": USER, "format": "dxf", "region_code": "global",
        "metadata": {"source_file_id": SOURCE_FILE},
    }
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value={
            "id": PROJECT, "user_id": USER, "image_url": None, "workspace_id": None
        })),
        patch.object(pipeline, "_load_imported_dxf",
                     AsyncMock(return_value=(raw, SOURCE_FILE, 4))),
        patch.object(pipeline.storage_service, "upload_cad_file",
                     AsyncMock(return_value="https://storage.example/reference.dxf")) as upload,
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client",
                     return_value=(MagicMock(), "dxf-files", "global")),
        patch.object(pipeline, "create_artifact_file",
                     AsyncMock(return_value={"id": "file-artifact-12"})),
        patch.object(pipeline, "update_export_status",
                     AsyncMock(return_value={"artifact_file_id": "file-artifact-12"})) as persist,
    ):
        result = await pipeline.run_export_generation(job)
    assert upload.await_args.kwargs["file_bytes"] == raw
    assert result["generation_method"] == "verified_imported_dxf"
    assert result["source_insunits"] == 4
    assert result["source_file_id"] == SOURCE_FILE
    assert result["engineering_accuracy_verified"] is False
    assert persist.await_args.args[1]["metadata"]["generation_method"] == "verified_imported_dxf"


@pytest.mark.asyncio
async def test_dxf_source_does_not_fall_back_to_image_when_job_unavailable():
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value={
            "id": PROJECT, "user_id": USER, "image_url": "data:image/png;base64,test",
            "workspace_id": None
        })),
        patch.object(pipeline, "_load_imported_dxf",
                     AsyncMock(side_effect=RuntimeError("source not found"))),
        patch.object(pipeline, "_generate_file", AsyncMock()) as raster,
    ):
        with pytest.raises(RuntimeError, match="source not found"):
            await pipeline.run_export_generation({
                "id": EXPORT, "source_job_id": SOURCE_JOB, "project_id": PROJECT,
                "requested_by": USER, "format": "dxf", "region_code": "global"
            })
    raster.assert_not_awaited()
