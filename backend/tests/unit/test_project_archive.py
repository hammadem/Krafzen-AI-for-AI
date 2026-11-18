"""Module 1/2: reliable listing and owned archive/restore endpoints."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from postgrest.exceptions import APIError

from app.db.queries import project_queries
from app.routes import project_routes

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
OTHER = "00000000-0000-0000-0000-000000000002"
PROJECT_ID = "00000000-0000-0000-0000-000000000011"
CREATED = "2026-11-18T00:00:00+00:00"
RECORD = {
    "id": PROJECT_ID, "user_id": USER["user_id"],
    "input_text": "Residential plan", "created_at": CREATED,
}


@pytest.mark.asyncio
async def test_active_projects_exclude_archived_and_archived_list_includes_only_archived():
    chain = MagicMock()
    chain.execute.return_value = SimpleNamespace(data=[RECORD])
    with (
        patch.object(project_queries, "db") as db,
        patch.object(project_queries, "run_in_threadpool", AsyncMock(side_effect=lambda fn: fn())),
    ):
        db.table.return_value = chain
        active = await project_queries.get_projects(USER)
        assert len(active) == 1
        chain.is_.assert_called_with("archived_at", "null")
        chain.reset_mock()
        archived = await project_queries.get_projects(USER, archived=True)
        assert len(archived) == 1
        chain.filter.assert_called_with("archived_at", "not.is", "null")


@pytest.mark.asyncio
async def test_db_outage_is_error_not_empty_project_list():
    with patch.object(project_queries, "run_in_threadpool", AsyncMock(side_effect=APIError({
        "message": "relation does not exist", "code": "42P01",
    }))):
        with pytest.raises(HTTPException) as exc:
            await project_queries.get_projects(USER)
    assert exc.value.status_code == 503


def test_invalid_status_filter_does_not_query_database(client):
    with patch.object(project_routes, "get_projects", AsyncMock()) as get:
        response = client.get("/api/v1/projects/?status=completed")
    assert response.status_code == 422
    get.assert_not_awaited()


def test_archive_route_denies_missing_or_foreign_project(client):
    with patch.object(project_routes, "archive_project", AsyncMock(return_value=None)):
        response = client.post(f"/api/v1/projects/{PROJECT_ID}/archive")
    assert response.status_code == 404


def test_restore_route_denies_missing_or_foreign_project(client):
    with patch.object(project_routes, "restore_project", AsyncMock(return_value=None)):
        response = client.post(f"/api/v1/projects/{PROJECT_ID}/restore")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_archive_db_mutation_is_scoped_to_owner():
    chain = MagicMock()
    chain.execute.return_value = SimpleNamespace(data=[{
        **RECORD, "archived_at": CREATED, "archived_by": USER["user_id"],
    }])
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value=RECORD)),
        patch.object(project_queries, "db") as db,
        patch.object(project_queries, "run_in_threadpool", AsyncMock(side_effect=lambda fn: fn())),
    ):
        db.table.return_value = chain
        out = await project_queries.archive_project(PROJECT_ID, USER)
        assert out["archived_by"] == USER["user_id"]
        chain.eq.assert_any_call("user_id", USER["user_id"])
        chain.is_.assert_called_with("archived_at", "null")


@pytest.mark.asyncio
async def test_restore_db_mutation_is_scoped_to_owner():
    chain = MagicMock()
    chain.execute.return_value = SimpleNamespace(data=[{
        **RECORD, "archived_at": None, "archived_by": None,
        "restored_at": CREATED, "restored_by": USER["user_id"],
    }])
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value={
            **RECORD, "archived_at": CREATED, "archived_by": USER["user_id"],
        })),
        patch.object(project_queries, "db") as db,
        patch.object(project_queries, "run_in_threadpool", AsyncMock(side_effect=lambda fn: fn())),
    ):
        db.table.return_value = chain
        out = await project_queries.restore_project(PROJECT_ID, USER)
        assert out["archived_at"] is None
        chain.eq.assert_any_call("user_id", USER["user_id"])
        chain.filter.assert_called_with("archived_at", "not.is", "null")


@pytest.mark.asyncio
async def test_archive_blocked_before_write_when_not_owned():
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value=None)),
        patch.object(project_queries, "run_in_threadpool", AsyncMock()) as run,
    ):
        assert await project_queries.archive_project(PROJECT_ID, USER) is None
    run.assert_not_awaited()


def test_archive_http_route_returns_edited_record(client):
    record = {**RECORD, "archived_at": CREATED, "archived_by": USER["user_id"]}
    with patch.object(project_routes, "archive_project", AsyncMock(return_value=record)):
        response = client.post(f"/api/v1/projects/{PROJECT_ID}/archive")
    assert response.status_code == 200
    assert response.json()["archived_by"] == USER["user_id"]
