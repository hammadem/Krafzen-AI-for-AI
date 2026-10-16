from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.models.activity_model import ActivityEventResponse
from app.services import activity_service


class FakeInsertQuery:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return SimpleNamespace(data=[self.payload])


class FakeActivityTable:
    def __init__(self):
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        return FakeInsertQuery(payload)


class FakeDatabase:
    def __init__(self):
        self.activity_table = FakeActivityTable()

    def table(self, table_name):
        assert table_name == "activity_events"
        return self.activity_table


class FakeReadQuery:
    def __init__(self, data):
        self.data = data
        self.filters = []

    def select(self, _columns):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def maybe_single(self):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, _limit):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeWorkspaceDatabase:
    def __init__(self):
        self.workspace_query = FakeReadQuery({"owner_id": "owner"})
        self.membership_query = FakeReadQuery({
            "user_id": "00000000-0000-0000-0000-000000000004"
        })
        self.activity_data = [{
            "event_id": "00000000-0000-0000-0000-000000000001",
            "action": "member.joined",
            "entity_type": "member",
            "entity_id": "00000000-0000-0000-0000-000000000002",
            "organization_id": "00000000-0000-0000-0000-000000000003",
            "timestamp": "2026-10-07T19:10:40+00:00",
        }]
        self.activity_queries = []

    def table(self, table_name):
        if table_name == "workspaces":
            return self.workspace_query
        if table_name == "workspace_members":
            return self.membership_query
        if table_name == "activity_events":
            query = FakeReadQuery(self.activity_data)
            self.activity_queries.append(query)
            return query
        raise AssertionError(f"Unexpected table: {table_name}")


@pytest.mark.asyncio
async def test_record_event_writes_canonical_and_legacy_shapes(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(activity_service, "db", fake_db)

    async def run_inline(function):
        return function()

    monkeypatch.setattr(activity_service, "run_in_threadpool", run_inline)

    event = await activity_service.record_event(
        action="export.completed",
        entity_type="export_job",
        entity_id="00000000-0000-0000-0000-000000000001",
        organization_id="00000000-0000-0000-0000-000000000002",
        project_id="00000000-0000-0000-0000-000000000003",
        actor_user_id="00000000-0000-0000-0000-000000000004",
        metadata={"source": "worker"},
    )

    payload = fake_db.activity_table.payload
    assert payload["event_id"] == payload["id"]
    assert payload["action"] == payload["event_name"] == "export.completed"
    assert payload["entity_type"] == "export_job"
    assert payload["entity_id"] == payload["job_id"]
    assert payload["organization_id"] == "00000000-0000-0000-0000-000000000002"
    assert payload["timestamp"] == payload["created_at"]
    assert datetime.fromisoformat(payload["timestamp"]).utcoffset() == timedelta(0)
    assert event["event_id"] == event["id"]
    assert event["action"] == event["event_name"] == "export.completed"
    api_event = ActivityEventResponse.model_validate(event)
    assert api_event.entity_type == "export_job"
    assert api_event.entity_id == payload["entity_id"]


@pytest.mark.asyncio
async def test_record_audit_event_persists_requested_audit_fields(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(activity_service, "db", fake_db)

    async def run_inline(function):
        return function()

    monkeypatch.setattr(activity_service, "run_in_threadpool", run_inline)

    event = await activity_service.record_audit_event(
        actor_user_id="00000000-0000-0000-0000-000000000004",
        organization_id="00000000-0000-0000-0000-000000000005",
        project_id="00000000-0000-0000-0000-000000000006",
        action="file.renamed",
        entity_type="file",
        entity_id="00000000-0000-0000-0000-000000000007",
        metadata={"old_name": "plan.dxf", "new_name": "floor-plan.dxf"},
    )

    row = fake_db.activity_table.payload
    assert row["actor_user_id"] == event["actor_user_id"]
    assert row["organization_id"] == event["organization_id"]
    assert row["project_id"] == event["project_id"]
    assert row["action"] == event["action"] == "file.renamed"
    assert row["entity_type"] == event["entity_type"] == "file"
    assert row["entity_id"] == event["entity_id"] == "00000000-0000-0000-0000-000000000007"
    assert row["timestamp"] == event["timestamp"]
    assert row["metadata"] == event["metadata"]


@pytest.mark.asyncio
async def test_record_event_maps_legacy_export_arguments(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(activity_service, "db", fake_db)

    async def run_inline(function):
        return function()

    monkeypatch.setattr(activity_service, "run_in_threadpool", run_inline)

    await activity_service.record_event(
        "export.completed",
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
    )

    payload = fake_db.activity_table.payload
    assert payload["action"] == "export.completed"
    assert payload["entity_type"] == "export_job"
    assert payload["entity_id"] == payload["job_id"]
    assert payload["project_id"] == "00000000-0000-0000-0000-000000000002"


@pytest.mark.asyncio
async def test_file_event_uses_file_reference_from_metadata(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(activity_service, "db", fake_db)

    async def run_inline(function):
        return function()

    monkeypatch.setattr(activity_service, "run_in_threadpool", run_inline)

    await activity_service.record_event(
        action="file.renamed",
        project_id="00000000-0000-0000-0000-000000000001",
        metadata={"file_id": "00000000-0000-0000-0000-000000000002"},
    )

    payload = fake_db.activity_table.payload
    assert payload["entity_type"] == "file"
    assert payload["entity_id"] == "00000000-0000-0000-0000-000000000002"


@pytest.mark.asyncio
async def test_file_event_requires_its_own_entity_reference(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(activity_service, "db", fake_db)

    with pytest.raises(ValueError, match="entity_id is required"):
        await activity_service.record_event(
            action="file.updated",
            project_id="00000000-0000-0000-0000-000000000001",
        )

    assert fake_db.activity_table.payload is None


def test_shape_activity_row_keeps_legacy_aliases():
    timestamp = "2026-10-07T19:10:40+00:00"
    shaped = activity_service._shape_activity_row({
        "id": "00000000-0000-0000-0000-000000000001",
        "event_name": "export.completed",
        "job_id": "00000000-0000-0000-0000-000000000002",
        "created_at": timestamp,
        "metadata": {"source": "worker"},
    })

    assert shaped["event_id"] == shaped["id"]
    assert shaped["action"] == shaped["event_name"] == "export.completed"
    assert shaped["entity_type"] == "export_job"
    assert shaped["entity_id"] == shaped["job_id"]
    assert shaped["timestamp"] == shaped["created_at"] == timestamp


@pytest.mark.asyncio
async def test_workspace_activity_is_filtered_by_organization_id(monkeypatch):
    fake_db = FakeWorkspaceDatabase()
    monkeypatch.setattr(activity_service, "db", fake_db)

    async def run_inline(function):
        return function()

    monkeypatch.setattr(activity_service, "run_in_threadpool", run_inline)

    activity = await activity_service.get_workspace_activity(
        workspace_id="00000000-0000-0000-0000-000000000003",
        user_id="00000000-0000-0000-0000-000000000004",
    )

    assert any(
        query.filters
        == [("organization_id", "00000000-0000-0000-0000-000000000003")]
        for query in fake_db.activity_queries
    )
    assert activity[0]["action"] == "member.joined"
