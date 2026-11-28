"""End-to-end API contract tests for authenticated export history, retry and download.

These run with mocked database/storage; live Supabase and CAD file E2E still
require an isolated staging environment.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from fastapi import HTTPException

from app.db.queries import export_queries
from app.routes import export_routes

USER_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"
EXPORT_ID = "00000000-0000-0000-0000-000000000003"
FILE_ID = "00000000-0000-0000-0000-000000000004"

SAMPLE = {
    "id": EXPORT_ID, "project_id": PROJECT_ID, "requested_by": USER_ID,
    "format": "dxf", "status": "failed", "retry_count": 0,
    "artifact_file_id": None, "idempotency_key": "export-test-12345",
    "metadata": {"stage": "export_generation", "region_code": "global"},
}


@pytest.mark.asyncio
async def test_my_export_list_is_requester_scoped_and_paginated():
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.execute.return_value = SimpleNamespace(data=[SAMPLE])
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(export_queries, "db", db),
        patch.object(export_queries, "run_in_threadpool", inline),
    ):
        result = await export_queries.list_user_exports(USER_ID, page=3, limit=20)
    assert result == [SAMPLE]
    query.eq.assert_called_once_with("requested_by", USER_ID)
    query.range.assert_called_once_with(40, 59)


@pytest.mark.asyncio
async def test_retry_resets_artifacts_and_increments_attempt_atomically():
    query = MagicMock()
    query.update.return_value = query
    query.eq.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{
        **SAMPLE, "status": "queued", "retry_count": 1
    }])
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(export_queries, "get_export", AsyncMock(return_value={
            **SAMPLE, "artifact_file_id": FILE_ID,
            "file_path": "legacy-path", "error_message": "old error",
        })),
        patch.object(export_queries, "db", db),
        patch.object(export_queries, "run_in_threadpool", inline),
    ):
        result = await export_queries.retry_export(EXPORT_ID, USER_ID)

    assert result["status"] == "queued"
    payload = query.update.call_args.args[0]
    assert payload["artifact_file_id"] is None
    assert payload["file_path"] is None
    assert payload["error_message"] is None
    assert payload["progress_percent"] == 0
    assert payload["retry_count"] == 1
    assert "stage" not in payload["metadata"]
    assert payload["metadata"]["region_code"] == "global"
    assert call("id", EXPORT_ID) in query.eq.call_args_list
    assert call("requested_by", USER_ID) in query.eq.call_args_list
    assert call("status", "failed") in query.eq.call_args_list


@pytest.mark.asyncio
async def test_retry_rejects_concurrent_claim():
    query = MagicMock()
    query.update.return_value = query
    query.eq.return_value = query
    query.execute.return_value = SimpleNamespace(data=[])
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(export_queries, "get_export", AsyncMock(return_value=SAMPLE)),
        patch.object(export_queries, "db", db),
        patch.object(export_queries, "run_in_threadpool", inline),
    ):
        with pytest.raises(HTTPException) as exc:
            await export_queries.retry_export(EXPORT_ID, USER_ID)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["processing", "validating", "completed"])
async def test_retry_rejects_nonterminal_state(state):
    with patch.object(
        export_queries, "get_export", AsyncMock(return_value={**SAMPLE, "status": state})
    ):
        with pytest.raises(HTTPException) as exc:
            await export_queries.retry_export(EXPORT_ID, USER_ID)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_retry_limited_and_duplicate_queued_is_idempotent():
    with patch.object(
        export_queries, "get_export",
        AsyncMock(return_value={**SAMPLE, "retry_count": 3})
    ):
        with pytest.raises(HTTPException) as exc:
            await export_queries.retry_export(EXPORT_ID, USER_ID)
    assert exc.value.status_code == 409

    queued = {**SAMPLE, "status": "queued"}
    with patch.object(export_queries, "get_export", AsyncMock(return_value=queued)):
        assert await export_queries.retry_export(EXPORT_ID, USER_ID) is queued


@pytest.mark.asyncio
async def test_retry_preserves_requester_permission_gate():
    with patch.object(
        export_queries, "get_export",
        AsyncMock(side_effect=HTTPException(status_code=403, detail="Access denied")),
    ):
        with pytest.raises(HTTPException) as exc:
            await export_queries.retry_export(EXPORT_ID, USER_ID)
    assert exc.value.status_code == 403


def _sample_export_and_artifact():
    export = {**SAMPLE, "status": "completed", "artifact_file_id": FILE_ID}
    artifact = {
        "id": FILE_ID, "project_id": PROJECT_ID, "job_id": EXPORT_ID,
        "path": f"{USER_ID}/{PROJECT_ID}/export.dxf",
        "bucket": "dxf-files", "name": "export.dxf",
        "file_type": "dxf", "size_bytes": 256,
    }
    return export, artifact


@pytest.mark.asyncio
async def test_signed_download_is_scoped_to_export_not_regular_job():
    export, artifact = _sample_export_and_artifact()
    storage = MagicMock()
    storage.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://example.invalid/signed"
    }

    async def inline(fn):
        return fn()

    with (
        patch.object(export_routes, "get_export_artifact", AsyncMock(return_value=artifact)),
        patch.object(export_routes, "get_export", AsyncMock(return_value=export)),
        patch.object(
            export_routes, "_resolve_project_residency_context",
            AsyncMock(return_value={"organization_id": None, "region_code": "global"}),
        ),
        patch.object(
            export_routes.storage_service, "resolve_target_bucket_and_client",
            return_value=(storage, "dxf-files", "global"),
        ),
        patch.object(export_routes, "run_in_threadpool", inline),
    ):
        result = await export_routes.get_export_artifact_route(
            EXPORT_ID, user={"user_id": USER_ID}
        )
    assert result["signed_url"] == "https://example.invalid/signed"
    storage.storage.from_.return_value.create_signed_url.assert_called_once_with(
        path=artifact["path"], expires_in=3600
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_field,bad_value", [
    ("path", "../../private/key.dxf"),
    ("path", f"{USER_ID}/{PROJECT_ID}/nested\\escape.dxf"),
    ("bucket", "another-tenant-bucket"),
    ("project_id", "00000000-0000-0000-0000-000000000009"),
    ("job_id", "00000000-0000-0000-0000-000000000008"),
])
async def test_signed_download_rejects_unbound_or_unsafe_artifact(bad_field, bad_value):
    export, artifact = _sample_export_and_artifact()
    artifact[bad_field] = bad_value
    storage = MagicMock()
    with (
        patch.object(export_routes, "get_export_artifact", AsyncMock(return_value=artifact)),
        patch.object(export_routes, "get_export", AsyncMock(return_value=export)),
        patch.object(
            export_routes, "_resolve_project_residency_context",
            AsyncMock(return_value={"organization_id": None, "region_code": "global"}),
        ),
        patch.object(
            export_routes.storage_service, "resolve_target_bucket_and_client",
            return_value=(storage, "dxf-files", "global"),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await export_routes.get_export_artifact_route(EXPORT_ID, user={"user_id": USER_ID})
    assert exc.value.status_code == 409
    storage.storage.from_.return_value.create_signed_url.assert_not_called()


@pytest.mark.asyncio
async def test_signed_download_rejects_incomplete_export():
    export, artifact = _sample_export_and_artifact()
    export["status"] = "failed"
    with (
        patch.object(export_routes, "get_export_artifact", AsyncMock(return_value=artifact)),
        patch.object(export_routes, "get_export", AsyncMock(return_value=export)),
        patch.object(
            export_routes, "_resolve_project_residency_context",
            AsyncMock(return_value={"organization_id": None, "region_code": "global"}),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await export_routes.get_export_artifact_route(EXPORT_ID, user={"user_id": USER_ID})
    assert exc.value.status_code == 409


def test_http_export_history_is_authenticated(client):
    with patch.object(export_routes, "list_user_exports", AsyncMock(return_value=[SAMPLE])) as list_it:
        response = client.get("/api/v1/exports/?page=2&limit=10")
    assert response.status_code == 200
    assert response.json()[0]["id"] == EXPORT_ID
    list_it.assert_awaited_once_with(USER_ID, page=2, limit=10)


def test_http_export_retry_routes_to_owned_workflow(client):
    with patch.object(
        export_routes, "retry_export",
        AsyncMock(return_value={**SAMPLE, "status": "queued", "retry_count": 1}),
    ) as retry:
        response = client.post(f"/api/v1/exports/{EXPORT_ID}/retry")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    retry.assert_awaited_once_with(EXPORT_ID, USER_ID)
