"""DXF import gates: no live Supabase, scanner or object storage needed."""

import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import ezdxf
import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.services import import_service

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
PROJECT = "00000000-0000-0000-0000-000000000002"
JOB = "00000000-0000-0000-0000-000000000003"


def make_upload(data: bytes, filename: str = "drawing.dxf"):
    return UploadFile(filename=filename, file=io.BytesIO(data))


def valid_dxf(tmp_path):
    path = tmp_path / "geometry.dxf"
    doc = ezdxf.new("R2010")
    doc.modelspace().add_line((0, 0), (10, 10))
    doc.saveas(path)
    return path.read_bytes()


@pytest.mark.asyncio
async def test_unsupported_filename_rejected_without_storage():
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client") as storage,
    ):
        with pytest.raises(HTTPException) as exc:
            await import_service.import_dxf_for_job(
                job_id=JOB, upload=make_upload(b"PDF", "unsafe.pdf"), user=USER
            )
    assert exc.value.status_code == 415
    storage.assert_not_called()


@pytest.mark.asyncio
async def test_cross_user_job_blocked_before_reading_upload():
    with patch.object(import_service, "get_job", AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as exc:
            await import_service.import_dxf_for_job(
                job_id=JOB, upload=make_upload(b"data"), user=USER
            )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_org_imports_fail_closed_before_storage():
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": "org-id"})),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client") as storage,
    ):
        with pytest.raises(HTTPException) as exc:
            await import_service.import_dxf_for_job(
                job_id=JOB, upload=make_upload(b"data"), user=USER
            )
    assert exc.value.status_code == 503
    storage.assert_not_called()


@pytest.mark.asyncio
async def test_oversized_upload_fails_before_scanner():
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service, "_scan_and_validate") as scanner,
    ):
        with pytest.raises(HTTPException) as exc:
            await import_service.import_dxf_for_job(
                job_id=JOB, upload=make_upload(b"x" * (import_service.MAX_DXF_BYTES + 1)),
                user=USER,
            )
    assert exc.value.status_code == 413
    scanner.assert_not_called()


def test_dxf_scanner_missing_denies_upload(tmp_path):
    content = valid_dxf(tmp_path)
    with patch.object(import_service.shutil, "which", return_value=None):
        with pytest.raises(HTTPException) as exc:
            import_service._scan_and_validate(content)
    assert exc.value.status_code == 503


def test_dxf_scanner_rejects_malware(tmp_path):
    content = valid_dxf(tmp_path)
    with (
        patch.object(import_service.shutil, "which", return_value="/usr/bin/clamscan"),
        patch.object(import_service.subprocess, "run", return_value=SimpleNamespace(returncode=1)),
    ):
        with pytest.raises(HTTPException) as exc:
            import_service._scan_and_validate(content)
    assert exc.value.status_code == 422


def test_real_dxf_parser_accepts_geometry_after_clean_scan(tmp_path):
    content = valid_dxf(tmp_path)
    with (
        patch.object(import_service.shutil, "which", return_value="/usr/bin/clamscan"),
        patch.object(import_service.subprocess, "run", return_value=SimpleNamespace(returncode=0)),
    ):
        import_service._scan_and_validate(content)


def test_dxf_parser_rejects_empty_modelspace(tmp_path):
    path = tmp_path / "empty.dxf"
    ezdxf.new("R2010").saveas(path)
    with (
        patch.object(import_service.shutil, "which", return_value="/usr/bin/clamscan"),
        patch.object(import_service.subprocess, "run", return_value=SimpleNamespace(returncode=0)),
    ):
        with pytest.raises(HTTPException) as exc:
            import_service._scan_and_validate(path.read_bytes())
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_successful_dxf_import_uploads_then_registers_file(tmp_path):
    content = valid_dxf(tmp_path)
    client = MagicMock()
    client.storage.from_.return_value.upload.return_value = {"path": "ok"}
    record = {"id": "file-1", "job_id": JOB, "project_id": PROJECT, "name": "drawing.dxf"}
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service, "_scan_and_validate"),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client", return_value=(client, "dxf-files", "global")),
        patch.object(import_service, "create_file", AsyncMock(return_value=record)) as save,
    ):
        result = await import_service.import_dxf_for_job(
            job_id=JOB, upload=make_upload(content), user=USER
        )
    assert result["id"] == "file-1"
    file_payload = save.await_args.args[0]
    assert file_payload["bucket"] == "dxf-files"
    assert file_payload["path"].startswith(f"{USER['user_id']}/{PROJECT}/imports/{JOB}/")
    assert file_payload["size_bytes"] == len(content)
    assert client.storage.from_.return_value.upload.call_count == 1


@pytest.mark.asyncio
async def test_failed_metadata_save_cleans_up_uploaded_object(tmp_path):
    content = valid_dxf(tmp_path)
    client = MagicMock()
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service, "_scan_and_validate"),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client", return_value=(client, "dxf-files", "global")),
        patch.object(import_service, "create_file", AsyncMock(return_value={"error": "db failed"})),
    ):
        with pytest.raises(HTTPException) as exc:
            await import_service.import_dxf_for_job(
                job_id=JOB, upload=make_upload(content), user=USER
            )
    assert exc.value.status_code == 503
    assert client.storage.from_.return_value.remove.call_count == 1
