from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.db.queries import file_queries

USER_ID = "00000000-0000-0000-0000-000000000001"
JOB_ID = "00000000-0000-0000-0000-000000000002"
PROJECT_ID = "00000000-0000-0000-0000-000000000003"
FILE_ID = "00000000-0000-0000-0000-000000000004"
REVIEWER_ID = "00000000-0000-0000-0000-000000000005"


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
        patch.object(
            file_queries,
            "_get_owned_job_project_id",
            AsyncMock(return_value=PROJECT_ID),
        ),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=db_results[1]),
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
    assert "path" not in rename_metadata
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
        patch.object(
            file_queries,
            "_get_owned_job_project_id",
            AsyncMock(return_value=PROJECT_ID),
        ),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=db_results[1]),
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
        "reviewed_by": REVIEWER_ID,
    }
    approved_file = {
        **file_row,
        "approval_state": "approved",
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
    assert event["metadata"]["reviewed_by"] == REVIEWER_ID
    assert event["metadata"]["approved_by"] == USER_ID


@pytest.mark.asyncio
async def test_file_rename_surfaces_audit_failure_after_successful_mutation():
    file_row = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "name": "floor-plan.dwg",
        "path": "uploads/floor-plan.dwg",
        "file_type": "dwg",
        "version": 1,
    }
    updated_file = {**file_row, "name": "floor-plan-final.dwg"}

    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file_row)),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[updated_file])),
        ),
        patch.object(
            file_queries,
            "record_audit_event",
            AsyncMock(side_effect=RuntimeError("audit store unavailable")),
        ),
        pytest.raises(HTTPException) as error,
    ):
        await file_queries.update_file(
            FILE_ID,
            {"name": "floor-plan-final.dwg"},
            {"user_id": USER_ID},
        )

    assert error.value.status_code == 500
    assert "File state changed but file.renamed audit event could not be recorded" in str(error.value.detail)


@pytest.mark.asyncio
async def test_revision_review_is_a_separate_audit_event():
    file_row = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "version": 3,
        "approval_state": "pending_review",
        "reviewed_by": None,
    }
    reviewed_file = {
        **file_row,
        "reviewed_by": REVIEWER_ID,
        "reviewed_at": "2026-10-24T12:00:00+00:00",
    }
    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file_row)),
        patch.object(
            file_queries,
            "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[reviewed_file])),
        ),
        patch.object(
            file_queries, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        result = await file_queries.mark_revision_reviewed(
            FILE_ID, {"user_id": REVIEWER_ID}
        )

    assert result == reviewed_file
    event = record_event.await_args.kwargs
    assert event["action"] == "revision.reviewed"
    assert event["actor_user_id"] == REVIEWER_ID
    assert event["metadata"]["reviewed_by"] == REVIEWER_ID
    assert event["metadata"]["approval_state"] == "pending_review"


@pytest.mark.asyncio
async def test_revision_cannot_be_approved_before_review():
    from fastapi import HTTPException

    file_row = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_ID,
        "approval_state": "pending_review",
        "reviewed_by": None,
    }
    with (
        patch.object(file_queries, "get_file", AsyncMock(return_value=file_row)),
        patch.object(file_queries, "record_audit_event", AsyncMock()) as record_event,
        pytest.raises(HTTPException) as error,
    ):
        await file_queries.set_revision_approval(
            FILE_ID, "approved", {"user_id": USER_ID}
        )

    assert error.value.status_code == 409
    record_event.assert_not_awaited()


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
