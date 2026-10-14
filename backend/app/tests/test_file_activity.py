from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.db.queries import file_queries

USER_ID = "00000000-0000-0000-0000-000000000001"
JOB_ID = "00000000-0000-0000-0000-000000000002"
PROJECT_ID = "00000000-0000-0000-0000-000000000003"
FILE_ID = "00000000-0000-0000-0000-000000000004"


@pytest.mark.asyncio
async def test_create_file_records_upload_with_authoritative_project():
    file_row = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "path": "uploads/floor-plan.dwg",
        "name": "floor-plan.dwg",
        "file_type": "dwg",
        "version": 1,
    }
    db_results = [
        SimpleNamespace(data={"project_id": PROJECT_ID}),
        SimpleNamespace(data=[file_row]),
    ]

    with (
        patch.object(file_queries, "_user_owns_job", AsyncMock(return_value=True)),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(side_effect=db_results),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        result = await file_queries.create_file(
            {
                "job_id": JOB_ID,
                "project_id": PROJECT_ID,
                "path": "uploads/floor-plan.dwg",
                "file_type": "dwg",
            },
            {"user_id": USER_ID},
        )

    assert result == file_row
    assert [call.kwargs["action"] for call in record_event.await_args_list] == [
        "file.uploaded",
        "revision.created",
    ]
    event = record_event.await_args_list[0].kwargs
    assert event["action"] == "file.uploaded"
    assert event["entity_type"] == "file"
    assert event["entity_id"] == FILE_ID
    assert event["actor_user_id"] == USER_ID
    assert event["project_id"] == PROJECT_ID
    assert event["metadata"]["file_name"] == "floor-plan.dwg"
    assert event["metadata"]["file_type"] == "dwg"
    assert event["metadata"]["file_id"] == FILE_ID
    revision_event = record_event.await_args_list[1].kwargs
    assert revision_event["entity_type"] == "revision"
    assert revision_event["entity_id"] == FILE_ID
    assert revision_event["metadata"] == {
        "revision_id": FILE_ID,
        "file_id": FILE_ID,
        "version": 1,
        "approval_state": "pending_review",
    }


@pytest.mark.asyncio
async def test_update_file_records_rename_and_metadata_update():
    old_file = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "name": "floor-plan.dwg",
        "path": "uploads/floor-plan.dwg",
        "file_type": "dwg",
        "version": 1,
    }
    updated_file = {**old_file, "name": "floor-plan-final.dwg", "file_type": "dxf"}

    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=old_file)),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[updated_file])),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        result = await file_queries.update_file(
            FILE_ID,
            {"name": "floor-plan-final.dwg", "file_type": "dxf"},
            {"user_id": USER_ID},
        )

    assert result == updated_file
    assert [call.kwargs["action"] for call in record_event.await_args_list] == [
        "file.renamed",
        "file.updated",
    ]
    rename_metadata = record_event.await_args_list[0].kwargs["metadata"]
    assert rename_metadata["old_name"] == "floor-plan.dwg"
    assert rename_metadata["new_name"] == "floor-plan-final.dwg"
    assert record_event.await_args_list[1].kwargs["metadata"]["changed_fields"] == [
        "file_type"
    ]


@pytest.mark.asyncio
async def test_create_file_records_version_event_for_new_version():
    version_file = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "path": "uploads/floor-plan-v2.dwg",
        "name": "floor-plan.dwg",
        "file_type": "dwg",
        "version": 2,
    }
    db_results = [
        SimpleNamespace(data={"project_id": PROJECT_ID}),
        SimpleNamespace(data=[version_file]),
    ]

    with (
        patch.object(file_queries, "_user_owns_job", AsyncMock(return_value=True)),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(side_effect=db_results),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        await file_queries.create_file(
            {
                "job_id": JOB_ID,
                "path": "uploads/floor-plan-v2.dwg",
                "name": "floor-plan.dwg",
                "file_type": "dwg",
                "version": 2,
            },
            {"user_id": USER_ID},
        )

    assert [call.kwargs["action"] for call in record_event.await_args_list] == [
        "file.uploaded",
        "file.version_created",
        "revision.created",
    ]
    assert record_event.await_args_list[2].kwargs["metadata"]["version"] == 2


@pytest.mark.asyncio
async def test_archive_and_restore_record_state_transitions():
    file_row = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "path": "uploads/floor-plan.dwg",
        "name": "floor-plan.dwg",
        "file_type": "dwg",
        "version": 1,
    }
    archived_file = {**file_row, "archived_at": "2026-10-13T12:00:00+00:00"}
    with (
        patch.object(
            file_queries, "get_file", AsyncMock(side_effect=[file_row, archived_file])
        ),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(
                side_effect=[
                    SimpleNamespace(data=[archived_file]),
                    SimpleNamespace(data=[file_row]),
                ]
            ),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        assert await file_queries.archive_file(FILE_ID, {"user_id": USER_ID}) == archived_file
        assert await file_queries.restore_file(FILE_ID, {"user_id": USER_ID}) == file_row

    assert [call.kwargs["action"] for call in record_event.await_args_list] == [
        "file.archived",
        "file.restored",
        "revision.restored",
    ]


@pytest.mark.asyncio
async def test_revision_approval_persists_state_and_emits_reference_only_event():
    file_row = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "version": 3,
        "approval_state": "pending_review",
    }
    approved_file = {
        **file_row,
        "approval_state": "approved",
        "reviewed_by": USER_ID,
    }
    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file_row)),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[approved_file])),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        result = await file_queries.set_revision_approval(
            FILE_ID, "approved", {"user_id": USER_ID}
        )

    assert result == approved_file
    event = record_event.await_args.kwargs
    assert event["action"] == "revision.approved"
    assert event["entity_id"] == FILE_ID
    assert event["metadata"]["version"] == 3
    assert "path" not in event["metadata"]
    assert "name" not in event["metadata"]


@pytest.mark.asyncio
async def test_create_artifact_records_exported_source_file():
    artifact = {
        "id": "00000000-0000-0000-0000-000000000005",
        "project_id": PROJECT_ID,
        "name": "floor-plan-export.dxf",
        "file_type": "dxf",
        "version": 1,
    }
    with (
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[artifact])),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        result = await file_queries.create_artifact_file(
            {
                "project_id": PROJECT_ID,
                "name": artifact["name"],
                "file_type": "dxf",
                "source_file_id": FILE_ID,
                "source_file_name": "floor-plan.dwg",
            },
            USER_ID,
        )

    assert result == artifact
    event = record_event.await_args.kwargs
    assert event["action"] == "file.exported"
    assert event["entity_type"] == "file"
    assert event["entity_id"] == FILE_ID
    assert event["metadata"]["file_name"] == "floor-plan.dwg"
    assert event["metadata"]["export_format"] == "dxf"
    assert event["metadata"]["artifact_file_id"] == artifact["id"]
