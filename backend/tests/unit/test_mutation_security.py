"""HTTP and storage regression tests for untrusted customer mutations."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.db.queries import file_queries

JOB_ID = "00000000-0000-0000-0000-000000000003"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"
FILE_ID = "00000000-0000-0000-0000-000000000004"
USER_ID = "00000000-0000-0000-0000-000000000001"
USER = {"user_id": USER_ID}


def test_customer_cannot_change_file_storage_path_or_type(client):
    response = client.patch(f"/api/v1/files/{FILE_ID}", json={"path": "victim/path.dxf"})
    assert response.status_code == 422
    response = client.patch(f"/api/v1/files/{FILE_ID}", json={"file_type": "dwg"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_internal_file_update_cannot_change_path():
    with patch.object(file_queries, "get_file", AsyncMock(return_value={
        "id": FILE_ID, "job_id": JOB_ID, "project_id": PROJECT_ID, "path": "safe/file.dxf",
    })), patch.object(file_queries, "run_in_threadpool", AsyncMock()) as update:
        result = await file_queries.update_file(
            FILE_ID, {"path": f"{USER_ID}/{PROJECT_ID}/other.dxf"}, USER
        )
    assert "immutable" in result["error"]
    update.assert_not_awaited()


def test_customer_cannot_create_completed_job(client):
    response = client.post("/api/v1/jobs/", json={
        "project_id": PROJECT_ID, "status": "completed"
    })
    assert response.status_code == 422


def test_customer_cannot_patch_job_state(client):
    response = client.patch(f"/api/v1/jobs/{JOB_ID}", json={"status": "completed"})
    assert response.status_code == 422
    response = client.patch(f"/api/v1/jobs/{JOB_ID}", json={"error_message": "fake success"})
    assert response.status_code == 422


def test_customer_cannot_advance_job_state(client):
    with patch("app.routes.job_routes.advance_job_status", AsyncMock()) as advance:
        response = client.post(f"/api/v1/jobs/{JOB_ID}/advance", json={"status": "processing"})
    assert response.status_code == 403
    advance.assert_not_awaited()


@pytest.mark.asyncio
async def test_mismatched_project_file_metadata_is_denied():
    wrong_id = "00000000-0000-0000-0000-000000000099"
    row = {"id": FILE_ID, "job_id": JOB_ID, "project_id": wrong_id}
    with (
        patch.object(file_queries, "run_in_threadpool", AsyncMock(return_value=SimpleNamespace(data=row))),
        patch.object(file_queries, "_get_owned_job_project_id", AsyncMock(return_value=PROJECT_ID)),
    ):
        with pytest.raises(HTTPException) as error:
            await file_queries.get_file(FILE_ID, USER)
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_file_signing_rejects_other_user_path_and_arbitrary_bucket():
    storage = MagicMock()
    file = {
        "id": FILE_ID, "job_id": JOB_ID, "project_id": PROJECT_ID,
        "path": "another-user/another-project/private.dxf", "bucket": "dxf-files"
    }
    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file)),
        patch.object(file_queries, "_resolve_organization_id_for_file", AsyncMock(return_value=None)),
        patch.object(file_queries.storage_service, "resolve_target_bucket_and_client", return_value=(storage, "dxf-files", "global")),
    ):
        result = await file_queries.get_signed_url(FILE_ID, USER)
    assert result is None
    storage.storage.from_.assert_not_called()


@pytest.mark.asyncio
async def test_file_signing_rejects_bucket_switch_for_legacy_metadata():
    storage = MagicMock()
    file = {
        "id": FILE_ID, "job_id": JOB_ID, "project_id": PROJECT_ID,
        "path": f"{USER_ID}/{PROJECT_ID}/plan.dxf", "bucket": "other-tenant"
    }
    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file)),
        patch.object(file_queries, "_resolve_organization_id_for_file", AsyncMock(return_value=None)),
        patch.object(file_queries.storage_service, "resolve_target_bucket_and_client", return_value=(storage, "dxf-files", "global")),
    ):
        result = await file_queries.get_signed_url(FILE_ID, USER)
    assert result is None
    storage.storage.from_.assert_not_called()


@pytest.mark.asyncio
async def test_file_signing_uses_verified_bucket_and_prefix():
    storage = MagicMock()
    storage.storage.from_.return_value.create_signed_url.return_value = {"signedURL": "https://signed.example/token"}
    path = f"{USER_ID}/{PROJECT_ID}/imports/{JOB_ID}/plan.dxf"
    file = {
        "id": FILE_ID, "job_id": JOB_ID, "project_id": PROJECT_ID,
        "path": path, "bucket": "dxf-files"
    }
    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file)),
        patch.object(file_queries, "_resolve_organization_id_for_file", AsyncMock(return_value=None)),
        patch.object(file_queries.storage_service, "resolve_target_bucket_and_client", return_value=(storage, "dxf-files", "global")),
    ):
        result = await file_queries.get_signed_url(FILE_ID, USER)
    assert result == "https://signed.example/token"
    storage.storage.from_.assert_called_once_with("dxf-files")
    storage.storage.from_.return_value.create_signed_url.assert_called_once_with(path, 3600)
