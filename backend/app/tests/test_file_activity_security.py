from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.db.queries.file_queries import create_file, delete_file, update_file
from app.main import app
from app.routes.activity_routes import list_file_activity
from app.services import activity_service

USER_A = "00000000-0000-0000-0000-000000000001"
USER_B = "00000000-0000-0000-0000-000000000002"
PROJECT_B = "00000000-0000-0000-0000-000000000003"
WORKSPACE_B = "00000000-0000-0000-0000-000000000004"
JOB_ID = "00000000-0000-0000-0000-000000000005"
FILE_ID = "00000000-0000-0000-0000-000000000006"
USER = {"user_id": USER_A}


class StubQuery:
    def __init__(self, db, table):
        self.db = db
        self.table_name = table

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def maybe_single(self):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        self.db.queried_tables.append(self.table_name)
        return SimpleNamespace(data=self.db.responses.get(self.table_name))


class StubDB:
    def __init__(self, responses):
        self.responses = responses
        self.queried_tables = []

    def table(self, table_name):
        return StubQuery(self, table_name)


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_private_project_activity():
    db_stub = StubDB({"projects": None})
    with patch.object(activity_service, "db", db_stub):
        events = await activity_service.get_project_activity(PROJECT_B, USER_A)

    assert events == []
    assert db_stub.queried_tables == ["projects"]


@pytest.mark.asyncio
async def test_nonmember_and_removed_members_cannot_read_workspace_events():
    db_stub = StubDB({
        "workspaces": {"owner_id": USER_B},
        "workspace_members": None,
        "activity_events": [{"id": "private-event"}],
    })
    with patch.object(activity_service, "db", db_stub):
        events = await activity_service.get_workspace_activity(WORKSPACE_B, USER_A)

    assert events == []
    assert db_stub.queried_tables == ["workspaces", "workspace_members"]


@pytest.mark.asyncio
async def test_file_activity_route_checks_file_access_before_reading_events():
    with patch(
        "app.routes.activity_routes.get_file",
        new=AsyncMock(side_effect=HTTPException(status_code=403, detail="Access denied")),
    ), patch(
        "app.routes.activity_routes.get_file_activity",
        new=AsyncMock(),
    ) as read_activity:
        with pytest.raises(HTTPException) as error:
            await list_file_activity(FILE_ID, 50, USER)

    assert error.value.status_code == 403
    read_activity.assert_not_awaited()


@pytest.mark.asyncio
async def test_file_activity_route_uses_verified_file_job_and_project():
    file_record = {"id": FILE_ID, "job_id": JOB_ID, "project_id": PROJECT_B}
    expected_events = [{"id": "activity-1", "event_name": "file.uploaded"}]
    with patch(
        "app.routes.activity_routes.get_file",
        new=AsyncMock(return_value=file_record),
    ) as read_file, patch(
        "app.routes.activity_routes.get_file_activity",
        new=AsyncMock(return_value=expected_events),
    ) as read_activity:
        result = await list_file_activity(FILE_ID, 25, USER)

    assert result == expected_events
    read_file.assert_awaited_once_with(file_id=FILE_ID, user=USER)
    read_activity.assert_awaited_once_with(
        file_id=FILE_ID,
        job_id=JOB_ID,
        project_id=PROJECT_B,
        limit=25,
    )


@pytest.mark.asyncio
async def test_file_activity_combines_file_and_job_events_without_duplicates():
    file_event = {
        "id": "file-event",
        "event_name": "file.uploaded",
        "created_at": "2025-01-02T10:48:00+00:00",
        "profiles": {"display_name": "Khadija"},
    }
    job_event = {
        "id": "job-event",
        "event_name": "export.completed",
        "created_at": "2025-01-02T10:41:00+00:00",
    }
    db_stub = StubDB({"activity_events": [file_event, job_event]})

    with patch.object(activity_service, "db", db_stub):
        events = await activity_service.get_file_activity(FILE_ID, JOB_ID, PROJECT_B)

    assert [event["id"] for event in events] == ["file-event", "job-event"]
    assert events[0]["actor"]["display_name"] == "Khadija"
    assert db_stub.queried_tables == ["activity_events", "activity_events"]


@pytest.mark.asyncio
async def test_file_upload_audit_actor_comes_from_authenticated_user():
    created_file = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_B,
        "path": "projects/FloorPlan_V3.dwg",
        "name": "FloorPlan_V3.dwg",
    }
    with patch(
        "app.db.queries.file_queries._get_owned_job_project_id",
        new=AsyncMock(return_value=PROJECT_B),
    ), patch(
        "app.db.queries.file_queries.run_in_threadpool",
        new=AsyncMock(return_value=SimpleNamespace(data=[created_file])),
    ), patch(
        "app.db.queries.file_queries.record_audit_event",
        new=AsyncMock(return_value={"id": "activity-1"}),
    ) as record_event:
        result = await create_file(
            {
                "job_id": JOB_ID,
                "project_id": PROJECT_B,
                "path": created_file["path"],
                "actor_user_id": USER_B,
            },
            USER,
        )

    assert result == created_file
    upload_event = next(
        call.kwargs for call in record_event.await_args_list
        if call.kwargs["action"] == "file.uploaded"
    )
    assert upload_event["actor_user_id"] == USER_A
    assert upload_event["entity_id"] == FILE_ID
    assert upload_event["file_id"] == FILE_ID


@pytest.mark.asyncio
async def test_file_upload_rejects_a_project_id_that_does_not_match_its_job():
    with patch(
        "app.db.queries.file_queries._get_owned_job_project_id",
        new=AsyncMock(return_value=PROJECT_B),
    ), patch(
        "app.db.queries.file_queries.run_in_threadpool",
        new=AsyncMock(),
    ) as insert_file, pytest.raises(HTTPException) as error:
        await create_file(
            {"job_id": JOB_ID, "project_id": WORKSPACE_B, "path": "file.dwg"},
            USER,
        )

    assert error.value.status_code == 400
    insert_file.assert_not_awaited()


@pytest.mark.asyncio
async def test_file_rename_records_the_authenticated_actor():
    existing_file = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_B,
        "path": "projects/FloorPlan_V3.dwg",
        "name": "FloorPlan_V3.dwg",
    }
    updated_file = {**existing_file, "name": "FloorPlan_Final.dwg"}
    with patch(
        "app.db.queries.file_queries.get_file",
        new=AsyncMock(return_value=existing_file),
    ), patch(
        "app.db.queries.file_queries.run_in_threadpool",
        new=AsyncMock(return_value=SimpleNamespace(data=[updated_file])),
    ), patch(
        "app.db.queries.file_queries.record_audit_event",
        new=AsyncMock(return_value={"id": "activity-2"}),
    ) as record_event:
        result = await update_file(FILE_ID, {"name": "FloorPlan_Final.dwg"}, USER)

    assert result == updated_file
    rename_event = record_event.await_args.kwargs
    assert rename_event["action"] == "file.renamed"
    assert rename_event["actor_user_id"] == USER_A
    assert rename_event["metadata"]["old_name"] == "FloorPlan_V3.dwg"


@pytest.mark.asyncio
async def test_file_delete_records_the_authenticated_actor():
    existing_file = {
        "id": FILE_ID,
        "job_id": JOB_ID,
        "project_id": PROJECT_B,
        "path": "projects/FloorPlan_V3.dwg",
        "name": "FloorPlan_V3.dwg",
        "bucket": "krafzen-files",
    }
    with patch(
        "app.db.queries.file_queries.get_file",
        new=AsyncMock(return_value=existing_file),
    ), patch(
        "app.db.queries.file_queries.run_in_threadpool",
        new=AsyncMock(side_effect=[
            SimpleNamespace(data=[]),
            SimpleNamespace(data=[{"id": FILE_ID}]),
        ]),
    ), patch(
        "app.db.queries.file_queries.record_audit_event",
        new=AsyncMock(return_value={"id": "activity-3"}),
    ) as record_event:
        deleted = await delete_file(FILE_ID, USER)

    assert deleted is True
    assert record_event.await_args.kwargs["action"] == "file.deleted"
    assert record_event.await_args.kwargs["actor_user_id"] == USER_A
    assert record_event.await_args.kwargs["file_id"] == FILE_ID


def test_normal_users_have_read_only_activity_routes_and_database_grants():
    activity_routes = [
        route for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1/activity")
    ]
    assert activity_routes
    assert all(set(route.methods or []) <= {"GET", "HEAD"} for route in activity_routes)

    migration_dir = (
        Path(__file__).resolve().parent.parent
        / "db"
        / "migrations"
    )
    file_security_migration = (
        migration_dir / "011_file_activity_and_audit_security.sql"
    ).read_text(encoding="utf-8").upper()
    audit_contract_migration = (
        migration_dir / "010_activity_events_audit_contract.sql"
    ).read_text(encoding="utf-8").upper()
    read_scope_migration = (
        migration_dir / "013_activity_audit_read_scope.sql"
    ).read_text(encoding="utf-8").upper()

    assert "ENABLE ROW LEVEL SECURITY" in file_security_migration
    assert "REVOKE ALL PRIVILEGES" in read_scope_migration
    assert "FROM PUBLIC, ANON, AUTHENTICATED, SERVICE_ROLE" in read_scope_migration
    assert "GRANT SELECT, INSERT" in read_scope_migration
    assert "WORKSPACES.OWNER_ID = AUTH.UID()" in read_scope_migration
    assert "ON DELETE SET NULL" in file_security_migration
    assert "BEFORE UPDATE OR DELETE" in audit_contract_migration
    assert "BEFORE TRUNCATE" in audit_contract_migration
