"""
Tests for dashboard endpoints: activity feed, workspace summary, notifications, members.
Owner: Tazwar
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app
from app.schemas.export_contracts import ExportStatus

BASE = "/api/v1/dashboard"

MOCK_USER = {"user_id": "00000000-0000-0000-0000-000000000099", "email": "tazwar@test.com"}

MOCK_PROJECTS = [
    {"id": "00000000-0000-0000-0000-000000000002", "user_id": MOCK_USER["user_id"]}
]

MOCK_JOBS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "project_id": "00000000-0000-0000-0000-000000000002",
        "status": ExportStatus.COMPLETED.value,
        "updated_at": "2025-01-02T00:00:00",
        "created_at": "2025-01-01T00:00:00",
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "project_id": "00000000-0000-0000-0000-000000000002",
        "status": ExportStatus.FAILED.value,
        "updated_at": "2025-01-03T00:00:00",
        "created_at": "2025-01-01T00:00:00",
    },
]


@pytest.mark.asyncio
async def test_activity_feed_returns_correct_shape():
    with patch("app.routes.dashboard_routes.get_projects", new=AsyncMock(return_value=MOCK_PROJECTS)), \
         patch("app.routes.dashboard_routes.get_jobs", new=AsyncMock(return_value=MOCK_JOBS)), \
         patch("app.routes.dashboard_routes._get_user_workspace_ids", new=AsyncMock(return_value=[])), \
         patch("app.routes.dashboard_routes._get_activity_rows", new=AsyncMock(return_value=[])), \
         patch("app.routes.dashboard_routes._get_actor_names", new=AsyncMock(return_value={})), \
         patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/activity")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "total" in data
        assert data["total"] == len(MOCK_JOBS)
        event = data["events"][0]
        assert "job_id" in event
        assert "status" in event
        assert "message" in event
        assert "occurred_at" in event


@pytest.mark.asyncio
async def test_activity_feed_merges_workspace_events_and_export_statuses():
    audit_event = {
        "id": "event-1",
        "event_name": "file.uploaded",
        "project_id": MOCK_PROJECTS[0]["id"],
        "workspace_id": None,
        "actor_user_id": MOCK_USER["user_id"],
        "message": "Uploaded FloorPlan_V3.dwg",
        "metadata": {"file_name": "FloorPlan_V3.dwg"},
        "created_at": "2025-01-04T23:32:00+00:00",
    }
    with patch("app.routes.dashboard_routes.get_projects", new=AsyncMock(return_value=MOCK_PROJECTS)), \
         patch("app.routes.dashboard_routes.get_jobs", new=AsyncMock(return_value=MOCK_JOBS)), \
         patch("app.routes.dashboard_routes._get_user_workspace_ids", new=AsyncMock(return_value=["workspace-1"])), \
         patch("app.routes.dashboard_routes._get_activity_rows", new=AsyncMock(return_value=[audit_event])), \
         patch("app.routes.dashboard_routes._get_actor_names", new=AsyncMock(return_value={MOCK_USER["user_id"]: "Khadija Zain"})), \
         patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(BASE + "/activity")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    uploaded = next(event for event in data["events"] if event["id"] == "event-1")
    assert uploaded["category"] == "files"
    assert uploaded["actor_name"] == "Khadija Zain"
    assert uploaded["message"] == "Uploaded FloorPlan_V3.dwg"
    assert all(event["category"] == "exports" for event in data["events"] if event["id"] != "event-1")


@pytest.mark.asyncio
async def test_activity_feed_does_not_query_an_unowned_project():
    with patch("app.routes.dashboard_routes.get_projects", new=AsyncMock(return_value=MOCK_PROJECTS)), \
         patch("app.routes.dashboard_routes._get_user_workspace_ids", new=AsyncMock()) as get_workspace_ids, \
         patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                BASE + "/activity?project_id=00000000-0000-0000-0000-000000000999"
            )

    assert response.status_code == 200
    assert response.json() == {"events": [], "total": 0, "has_more": False}
    get_workspace_ids.assert_not_awaited()


@pytest.mark.asyncio
async def test_activity_feed_includes_audit_events():
    audit_event = {
        "event_id": "00000000-0000-0000-0000-000000000010",
        "action": "ai.generation_completed",
        "entity_type": "ai_generation",
        "entity_id": "00000000-0000-0000-0000-000000000011",
        "project_id": MOCK_PROJECTS[0]["id"],
        "timestamp": "2026-10-14T12:00:00+00:00",
        "actor_user_id": MOCK_USER["user_id"],
        "message": "AI generation completed",
        "metadata": {"generation_id": "00000000-0000-0000-0000-000000000011"},
    }
    with (
        patch(
            "app.routes.dashboard_routes.get_projects",
            new=AsyncMock(return_value=MOCK_PROJECTS),
        ),
        patch(
            "app.routes.dashboard_routes.get_jobs",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.routes.dashboard_routes._get_user_workspace_ids",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.routes.dashboard_routes._get_activity_rows",
            new=AsyncMock(return_value=[audit_event]),
        ),
        patch(
            "app.routes.dashboard_routes._get_actor_names",
            new=AsyncMock(return_value={}),
        ),
        patch("app.middlewares.auth.require_auth", return_value=MOCK_USER),
    ):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/activity")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    event = data["events"][0]
    assert event["action"] == "ai.generation_completed"
    assert event["event_type"] == "ai.generation_completed"
    assert event["entity_type"] == "ai_generation"
    assert event["entity_id"] == audit_event["entity_id"]


@pytest.mark.asyncio
async def test_activity_feed_pages_synthetic_history_without_gaps_or_duplicates():
    project_id = MOCK_PROJECTS[0]["id"]
    synthetic_events = [
        {
            "id": f"event-{index:04d}",
            "event_id": f"event-{index:04d}",
            "action": "ai.generation_completed",
            "entity_type": "ai_generation",
            "entity_id": f"generation-{index:04d}",
            "project_id": project_id,
            "timestamp": f"2026-10-01T00:{index // 60:02d}:{index % 60:02d}+00:00",
            "actor_user_id": MOCK_USER["user_id"],
            "message": f"Generated item {index}",
            "metadata": {},
        }
        for index in range(1, 1001)
    ]
    returned_ids: list[str] = []
    started = time.perf_counter()
    visible_projects = [
        MOCK_PROJECTS[0],
        {
            "id": "00000000-0000-0000-0000-000000000003",
            "user_id": MOCK_USER["user_id"],
        },
    ]
    with (
        patch(
            "app.routes.dashboard_routes.get_projects",
            new=AsyncMock(return_value=visible_projects),
        ),
        patch(
            "app.routes.dashboard_routes.get_jobs",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.routes.dashboard_routes._get_user_workspace_ids",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.routes.dashboard_routes._get_activity_rows",
            new=AsyncMock(return_value=synthetic_events),
        ),
        patch(
            "app.routes.dashboard_routes._get_actor_names",
            new=AsyncMock(return_value={}),
        ),
    ):
        async with AsyncClient(app=app, base_url="http://test") as client:
            for offset in range(0, len(synthetic_events), 50):
                response = await client.get(
                    f"{BASE}/activity?project_id={project_id}&limit=50&offset={offset}"
                )
                assert response.status_code == 200
                data = response.json()
                returned_ids.extend(event["event_id"] for event in data["events"])
                assert data["has_more"] is (offset + 50 < len(synthetic_events))

            other_project = visible_projects[1]["id"]
            response = await client.get(
                f"{BASE}/activity?project_id={other_project}&limit=50"
            )
            assert response.status_code == 200
            assert response.json()["events"] == []

    elapsed = time.perf_counter() - started
    assert len(returned_ids) == 1000
    assert len(set(returned_ids)) == 1000
    assert elapsed < 10


@pytest.mark.asyncio
async def test_workspace_summary_counts_by_status():
    with patch("app.routes.dashboard_routes.get_projects", new=AsyncMock(return_value=MOCK_PROJECTS)), \
         patch("app.routes.dashboard_routes.get_jobs", new=AsyncMock(return_value=MOCK_JOBS)), \
         patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/workspace-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] == 1
        assert data["total_jobs"] == 2
        assert data["jobs_by_status"]["completed"] == 1
        assert data["jobs_by_status"]["failed"] == 1
        assert data["requires_attention"] == 1  # only failed (no requires_review in mock)


NOTIFICATION_ID = "00000000-0000-0000-0000-000000000012"
PERSISTED_NOTIFICATION = {
    "id": NOTIFICATION_ID,
    "type": "import_completed",
    "message": "Imported and validated drawing.dxf",
    "is_read": False,
    "created_at": "2026-11-24T12:00:00+00:00",
}


@pytest.mark.asyncio
async def test_notifications_return_sunny_expected_shape():
    with patch("app.routes.dashboard_routes.get_notification_page", new=AsyncMock(return_value=([PERSISTED_NOTIFICATION], 1))) as get_page:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/notifications")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    notification = resp.json()["notifications"][0]
    assert notification == {
        "id": NOTIFICATION_ID, "title": "Import completed",
        "message": PERSISTED_NOTIFICATION["message"], "read": False,
        "created_at": PERSISTED_NOTIFICATION["created_at"], "type": "success",
    }
    assert get_page.await_args.args[1:] == (False, 20, 0)


@pytest.mark.asyncio
async def test_notifications_unread_only_filter():
    with patch("app.routes.dashboard_routes.get_notification_page", new=AsyncMock(return_value=([PERSISTED_NOTIFICATION], 5))) as get_page:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/notifications?unread_only=true&limit=1&offset=2")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5
    assert resp.json()["notifications"][0]["read"] is False
    assert get_page.await_args.args[1:] == (True, 1, 2)


@pytest.mark.asyncio
@pytest.mark.parametrize("updated,expected_status", [(True, 200), (False, 404)])
async def test_notification_read_updates_persisted_record(updated, expected_status):
    with patch("app.routes.dashboard_routes.mark_as_read", new=AsyncMock(return_value=updated)) as mark:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.patch(BASE + "/notifications/" + NOTIFICATION_ID + "/read")
    assert resp.status_code == expected_status
    assert mark.await_args.args[0] == NOTIFICATION_ID
    assert mark.await_args.args[1]
    if updated:
        assert resp.json() == {"id": NOTIFICATION_ID, "read": True}


@pytest.mark.asyncio
async def test_members_returns_at_least_owner():
    with patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/members")
        assert resp.status_code == 200
        data = resp.json()
        assert "members" in data
        assert data["total"] >= 1
        owner = data["members"][0]
        assert "user_id" in owner
        assert "role" in owner
        assert owner["role"] == "owner"