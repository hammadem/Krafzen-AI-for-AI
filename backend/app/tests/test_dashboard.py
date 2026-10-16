"""
Tests for dashboard endpoints: activity feed, workspace summary, notifications, members.
Owner: Tazwar
"""

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
    assert response.json() == {"events": [], "total": 0}
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


@pytest.mark.asyncio
async def test_notifications_return_sunny_expected_shape():
    with patch("app.routes.dashboard_routes.get_projects", new=AsyncMock(return_value=MOCK_PROJECTS)), \
         patch("app.routes.dashboard_routes.get_jobs", new=AsyncMock(return_value=MOCK_JOBS)), \
         patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert "notifications" in data
        assert "total" in data
        notif = data["notifications"][0]
        # Sunny's exact required fields
        assert "id" in notif
        assert "title" in notif
        assert "message" in notif
        assert "read" in notif
        assert "created_at" in notif
        assert "type" in notif
        assert notif["type"] in ("success", "error", "warning", "info")


@pytest.mark.asyncio
async def test_notifications_unread_only_filter():
    with patch("app.routes.dashboard_routes.get_projects", new=AsyncMock(return_value=MOCK_PROJECTS)), \
         patch("app.routes.dashboard_routes.get_jobs", new=AsyncMock(return_value=MOCK_JOBS)), \
         patch("app.middlewares.auth.require_auth", return_value=MOCK_USER):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get(BASE + "/notifications?unread_only=true")
        assert resp.status_code == 200
        data = resp.json()
        # All returned notifications must be unread
        for n in data["notifications"]:
            assert n["read"] is False


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